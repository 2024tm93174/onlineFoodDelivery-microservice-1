from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from pydantic import BaseModel
from app.database import SessionLocal, engine
from app.models import Base, Customer, Address

Base.metadata.create_all(bind=engine)
router = APIRouter(prefix="/customers/{customer_id}/addresses", tags=["addresses"])

class AddressIn(BaseModel):
    line1: str
    area: str
    city: str
    pincode: str

class AddressOut(AddressIn):
    address_id: int
    class Config:
        from_attributes = True

@router.get("", response_model=dict)
def list_addresses(customer_id: int, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    with SessionLocal() as db:
        if not db.get(Customer, customer_id):
            raise HTTPException(status_code=404, detail="Customer not found")
        stmt = select(Address).where(Address.customer_id==customer_id)
        total = db.scalar(stmt.count())
        items = db.execute(stmt.offset((page-1)*page_size).limit(page_size)).scalars().all()
        return {"items": [AddressOut.model_validate(i).model_dump() for i in items], "page": page, "page_size": page_size, "total": total}

@router.post("", response_model=AddressOut, status_code=201)
def create_address(customer_id: int, payload: AddressIn):
    with SessionLocal() as db:
        if not db.get(Customer, customer_id):
            raise HTTPException(status_code=404, detail="Customer not found")
        addr = Address(customer_id=customer_id, **payload.model_dump())
        db.add(addr)
        db.commit()
        db.refresh(addr)
        return AddressOut.model_validate(addr)
