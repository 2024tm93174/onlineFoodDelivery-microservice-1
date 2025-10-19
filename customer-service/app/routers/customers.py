from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import select
from app.database import SessionLocal, engine
from app.models import Base, Customer
from pydantic import BaseModel, EmailStr

Base.metadata.create_all(bind=engine)
router = APIRouter(prefix="/customers", tags=["customers"])

class CustomerIn(BaseModel):
    name: str
    email: EmailStr
    phone: str

class CustomerOut(BaseModel):
    customer_id: int
    name: str
    email: EmailStr
    phone: str
    class Config:
        from_attributes = True

@router.get("", response_model=dict)
def list_customers(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    with SessionLocal() as db:
        total = db.scalar(select(Customer).count())
        items = db.execute(select(Customer).offset((page-1)*page_size).limit(page_size)).scalars().all()
        return {"items": [CustomerOut.model_validate(i).model_dump() for i in items], "page": page, "page_size": page_size, "total": total}

@router.post("", response_model=CustomerOut, status_code=201)
def create_customer(payload: CustomerIn):
    with SessionLocal() as db:
        c = Customer(name=payload.name, email=payload.email, phone=payload.phone)
        db.add(c)
        db.commit()
        db.refresh(c)
        return CustomerOut.model_validate(c)

@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(customer_id: int):
    with SessionLocal() as db:
        c = db.get(Customer, customer_id)
        if not c:
            raise HTTPException(status_code=404, detail="Customer not found")
        return CustomerOut.model_validate(c)
