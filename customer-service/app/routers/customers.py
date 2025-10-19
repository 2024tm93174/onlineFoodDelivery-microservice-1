from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import select, func
from app.database import SessionLocal, engine
from app.models import Base, Customer
from pydantic import BaseModel, EmailStr


# IMPORTANT:
# Avoid creating tables at import time to prevent DB race conditions on startup.
# Use an app startup event elsewhere (e.g., in app/main.py) to run Base.metadata.create_all(bind=engine).

router = APIRouter(prefix="/v1/customers", tags=["customers"])


# ---------- Pydantic Schemas ----------

class CustomerIn(BaseModel):
    name: str
    email: EmailStr
    phone: str


class CustomerOut(BaseModel):
    customer_id: int
    name: str
    email: EmailStr
    phone: str


    # Pydantic v2 config style
    model_config = {"from_attributes": True}


# ---------- Endpoints ----------
@router.get("", response_model=dict)
def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Paginated list of customers.

    SQLAlchemy 2.x no longer supports `Select.count()`. Use `select(func.count(...))`.
    """
    with SessionLocal() as db:
        # Total rows
        total = db.scalar(select(func.count(Customer.customer_id))) or 0

        # Page of rows
        items = (
            db.execute(
                select(Customer)
                .order_by(Customer.customer_id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )

        return {
            "items": [CustomerOut.model_validate(i).model_dump() for i in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        }



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
