from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from app.database import SessionLocal, engine
from app.models import Base, Payment, IdempotencyKey
import hashlib, json, random, string

Base.metadata.create_all(bind=engine)
router = APIRouter(prefix="/payments", tags=["payments"])

class ChargeIn(BaseModel):
    order_id: int
    amount: float
    method: str

class ChargeOut(BaseModel):
    payment_id: int
    status: str
    reference: str
    class Config:
        from_attributes = True

def _hash(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

@router.post("/charge", response_model=ChargeOut)
def charge(payload: ChargeIn, Idempotency_Key: str = Header(..., convert_underscores=False)):
    if payload.method == "COD":
        # COD: mark pending until driver collects
        status = "PENDING"
    else:
        # succeed 90% for demo
        status = "SUCCESS" if random.random() < 0.9 else "FAILED"
    req_hash = _hash(payload.model_dump())

    with SessionLocal() as db:
        # idempotency check
        ike = db.execute(select(IdempotencyKey).where(IdempotencyKey.key==Idempotency_Key, IdempotencyKey.request_hash==req_hash)).scalar_one_or_none()
        if ike:
            return json.loads(ike.response_body)

        pay = Payment(order_id=payload.order_id, amount=payload.amount, method=payload.method, status=status,
                      reference="REF" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10)))
        db.add(pay); db.commit(); db.refresh(pay)
        resp = ChargeOut.model_validate(pay).model_dump()
        db.add(IdempotencyKey(key=Idempotency_Key, request_hash=req_hash, response_body=json.dumps(resp)))
        db.commit()
        if status == "FAILED":
            raise HTTPException(status_code=400, detail="Payment failed")
        return resp
