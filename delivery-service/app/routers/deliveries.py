from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from app.database import SessionLocal, engine
from app.models import Base, Driver, Delivery
from datetime import datetime

Base.metadata.create_all(bind=engine)
router = APIRouter(prefix="/deliveries", tags=["deliveries"])

class AssignIn(BaseModel):
    order_id: int
    city: str

class DeliveryOut(BaseModel):
    delivery_id: int
    order_id: int
    driver_id: int
    status: str
    class Config:
        from_attributes = True

@router.post("/assign", response_model=DeliveryOut, status_code=201)
def assign(payload: AssignIn):
    with SessionLocal() as db:
        # naive: pick first active driver
        drv = db.execute(select(Driver).where(Driver.is_active==True)).scalars().first()
        if not drv:
            raise HTTPException(status_code=503, detail="No drivers available")
        d = Delivery(order_id=payload.order_id, driver_id=drv.driver_id, status="ASSIGNED")
        db.add(d); db.commit(); db.refresh(d)
        return DeliveryOut.model_validate(d)

@router.post("/{delivery_id}/status")
def update_status(delivery_id: int, status: str):
    with SessionLocal() as db:
        d = db.get(Delivery, delivery_id)
        if not d: raise HTTPException(status_code=404, detail="Delivery not found")
        if status not in ["ASSIGNED","PICKED","DELIVERED"]:
            raise HTTPException(status_code=400, detail="Invalid status")
        d.status = status
        if status == "PICKED": d.picked_at = datetime.utcnow()
        if status == "DELIVERED": d.delivered_at = datetime.utcnow()
        db.commit()
        return { "delivery_id": d.delivery_id, "status": d.status }
