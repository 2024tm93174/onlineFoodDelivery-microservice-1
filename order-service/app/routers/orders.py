from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from app.database import SessionLocal, engine
from app.models import Base, Order, OrderItem
import httpx, os, math

Base.metadata.create_all(bind=engine)
router = APIRouter(prefix="/orders", tags=["orders"])

RESTAURANT_URL = os.getenv("RESTAURANT_SERVICE_URL", "http://restaurant-service:80")
PAYMENT_URL = os.getenv("PAYMENT_SERVICE_URL", "http://payment-service:80")
DELIVERY_URL = os.getenv("DELIVERY_SERVICE_URL", "http://delivery-service:80")
NOTIF_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:80")

TAX_RATE = 0.05
DELIVERY_FEE = 30.0

class OrderLineIn(BaseModel):
    item_id: int
    quantity: int

class PlaceOrderIn(BaseModel):
    customer_id: int
    restaurant_id: int
    address_id: int
    city: str
    lines: list[OrderLineIn]
    payment_method: str  # CARD|UPI|WALLET|COD

class OrderOut(BaseModel):
    order_id: int
    order_status: str
    payment_status: str
    order_total: float
    class Config:
        from_attributes = True

@router.get("", response_model=dict)
def list_orders(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    with SessionLocal() as db:
        total = db.scalar(select(Order).count())
        items = db.execute(select(Order).offset((page-1)*page_size).limit(page_size)).scalars().all()
        return { "items": [OrderOut.model_validate(o).model_dump() for o in items], "page": page, "page_size": page_size, "total": total }

@router.post("", response_model=OrderOut, status_code=201)
def place_order(payload: PlaceOrderIn, Idempotency_Key: str = Header(..., convert_underscores=False)):
    # business rules: max items per order 20, each qty <=5
    if len(payload.lines) > 20 or any(l.quantity > 5 or l.quantity < 1 for l in payload.lines):
        raise HTTPException(status_code=400, detail="Invalid quantities (max 20 lines, each qty 1..5).")

    # fetch restaurant & menu to validate availability and prices
    with httpx.Client(timeout=5.0) as client:
        r = client.get(f"{RESTAURANT_URL}/v1/restaurants/{payload.restaurant_id}")
        if r.status_code != 200:
            raise HTTPException(status_code=400, detail="Restaurant not found")
        rest = r.json()
        if not rest.get("is_open"):
            raise HTTPException(status_code=400, detail="Restaurant is closed")
        menu = client.get(f"{RESTAURANT_URL}/v1/restaurants/{payload.restaurant_id}/menu").json()["items"]

    # delivery must be same city as restaurant
    if rest.get("city") != payload.city:
        raise HTTPException(status_code=400, detail="Delivery city must match restaurant city")

    menu_by_id = {m["item_id"]: m for m in menu}
    # validate each requested item
    subtotal = 0.0
    for line in payload.lines:
        mi = menu_by_id.get(line.item_id)
        if not mi or not mi["is_available"]:
            raise HTTPException(status_code=400, detail=f"Item {line.item_id} not available")
        subtotal += mi["price"] * line.quantity

    tax = round(subtotal * TAX_RATE, 2)
    total = round(subtotal + tax + DELIVERY_FEE, 2)

    # create order (PENDING) with replicated snapshot fields
    with SessionLocal() as db:
        order = Order(customer_id=payload.customer_id, restaurant_id=payload.restaurant_id, address_id=payload.address_id,
                      order_status="PENDING", order_total=total, payment_status="INIT",
                      restaurant_name=rest["name"], address_city=payload.city)
        db.add(order); db.commit(); db.refresh(order)
        # items
        for line in payload.lines:
            mi = menu_by_id[line.item_id]
            db.add(OrderItem(order_id=order.order_id, item_id=line.item_id, quantity=line.quantity, price=mi["price"]))
        db.commit()

        # charge payment
        pay_req = { "order_id": order.order_id, "amount": total, "method": payload.payment_method }
        with httpx.Client(timeout=5.0) as client:
            pr = client.post(f"{PAYMENT_URL}/v1/payments/charge", headers={"Idempotency-Key": Idempotency_Key}, json=pay_req)
        if pr.status_code != 200:
            order.payment_status = "FAILED"; db.commit()
            raise HTTPException(status_code=400, detail="Payment failed")
        p = pr.json()
        order.payment_status = p.get("status", "FAILED")

        if order.payment_status == "SUCCESS" or payload.payment_method == "COD":
            order.order_status = "CONFIRMED"
            db.commit()
            # assign driver
            with httpx.Client(timeout=5.0) as client:
                client.post(f"{DELIVERY_URL}/v1/deliveries/assign", json={{"order_id": order.order_id, "city": payload.city}})
            # send notification
            with httpx.Client(timeout=3.0) as client:
                try:
                    client.post(f"{NOTIF_URL}/v1/notifications", json={{"order_id": order.order_id, "type": "ORDER_CONFIRMED"}})
                except Exception:
                    pass

        db.refresh(order)
        return OrderOut.model_validate(order)
