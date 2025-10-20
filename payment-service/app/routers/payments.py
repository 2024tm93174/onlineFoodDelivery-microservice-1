# payment-service/app/routers/payments.py

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from app.database import SessionLocal
from app.models import Payment, IdempotencyKey
import hashlib, json, random, string

router = APIRouter(prefix="/v1/payments", tags=["payments"])

class ChargeIn(BaseModel):
    order_id: int
    amount: float
    method: str  # CARD | UPI | WALLET | COD

class ChargeOut(BaseModel):
    payment_id: int
    status: str
    reference: str

    # Pydantic v2
    model_config = {"from_attributes": True}

def _hash(payload: dict) -> str:
    # stable hash across replays
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()

@router.post("/charge", response_model=ChargeOut)
def charge(
    payload: ChargeIn,
    # accept both spellings; one may be None
    idem_hyphen: str | None = Header(default=None, alias="Idempotency-Key", convert_underscores=False),
    idem_snake:  str | None = Header(default=None, alias="Idempotency_Key", convert_underscores=False),
):
    idempotency_key = idem_hyphen or idem_snake
    if not idempotency_key:
        # Make the requirement explicit in the error for users/tools
        raise HTTPException(status_code=422, detail="Idempotency key required in header as 'Idempotency-Key'")

    # Derive a status (demo); COD is PENDING
    if payload.method == "COD":
        status = "PENDING"
    else:
        status = "SUCCESS" if random.random() < 0.9 else "FAILED"

    req_hash = _hash(payload.model_dump())

    with SessionLocal() as db:
        # Idempotency: same key + same request -> return stored response
        existing = db.execute(
            select(IdempotencyKey).where(
                IdempotencyKey.key == idempotency_key,
                IdempotencyKey.request_hash == req_hash
            )
        ).scalar_one_or_none()
        if existing:
            try:
                return json.loads(existing.response_body)
            except Exception:
                # If legacy/garbled, just proceed to compute again but keep the same key
                pass

        # Create payment record
        pay = Payment(
            order_id=payload.order_id,
            amount=payload.amount,
            method=payload.method,
            status=status,
            reference="REF" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10)),
        )
        db.add(pay)
        db.commit()
        db.refresh(pay)

        resp = ChargeOut.model_validate(pay).model_dump()

        # Store idempotency response
        db.add(IdempotencyKey(
            key=idempotency_key,
            request_hash=req_hash,
            response_body=json.dumps(resp)
        ))
        db.commit()

        # Business error AFTER persistence -> return 400 cleanly (no crash)
        if status == "FAILED":
            raise HTTPException(status_code=400, detail="Payment failed")

        return resp
