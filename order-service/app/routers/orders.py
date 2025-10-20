# order-service/app/routers/orders.py

from fastapi import APIRouter, Header, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import select, func
from app.database import SessionLocal
from app.models import Order, OrderItem
import httpx
import os

# IMPORTANT:
# Don't call Base.metadata.create_all() here; it's done in app/main.py on startup.

# Expose all endpoints under /v1/orders
router = APIRouter(prefix="/v1/orders", tags=["orders"])

RESTAURANT_URL = os.getenv("RESTAURANT_SERVICE_URL", "http://restaurant-service:80")
PAYMENT_URL    = os.getenv("PAYMENT_SERVICE_URL",    "http://payment-service:80")
DELIVERY_URL   = os.getenv("DELIVERY_SERVICE_URL",   "http://delivery-service:80")
NOTIF_URL      = os.getenv("NOTIFICATION_SERVICE_URL","http://notification-service:80")

TAX_RATE = 0.05
DELIVERY_FEE = 30.0


# ---------- Schemas ----------

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

    # Pydantic v2 config
    model_config = {"from_attributes": True}


# ---------- Endpoints ----------

@router.get("", response_model=dict)
def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    with SessionLocal() as db:
        total = db.scalar(select(func.count(Order.order_id))) or 0
        items = (
            db.execute(
                select(Order)
                .order_by(Order.order_id.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )
        return {
            "items": [OrderOut.model_validate(o).model_dump() for o in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        }


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int):
    with SessionLocal() as db:
        o = db.get(Order, order_id)
        if not o:
            raise HTTPException(status_code=404, detail="Order not found")
        return OrderOut.model_validate(o)


@router.post("", response_model=OrderOut, status_code=201)
def place_order(
    payload: PlaceOrderIn,
    request: Request,
    idempotency_key: str = Header(
        ...,
        alias="Idempotency-Key",          # accept hyphenated header name
        convert_underscores=False
    ),
):
    # Business rules
    if len(payload.lines) < 1 or len(payload.lines) > 20:
        raise HTTPException(status_code=400, detail="Provide 1..20 order lines.")
    if any(l.quantity < 1 or l.quantity > 5 for l in payload.lines):
        raise HTTPException(status_code=400, detail="Each line quantity must be 1..5.")

    # Correlation ID propagation (best-effort)
    corr_id = request.headers.get("X-Correlation-ID")

    # Fetch restaurant & menu to validate availability and prices
    try:
        with httpx.Client(timeout=5.0) as client:
            r = client.get(
                f"{RESTAURANT_URL}/v1/restaurants/{payload.restaurant_id}",
                headers={"X-Correlation-ID": corr_id} if corr_id else None,
            )
            if r.status_code != 200:
                raise HTTPException(status_code=400, detail="Restaurant not found")

            rest = r.json()
            if not rest.get("is_open", False):
                raise HTTPException(status_code=400, detail="Restaurant is closed")

            mresp = client.get(
                f"{RESTAURANT_URL}/v1/restaurants/{payload.restaurant_id}/menu",
                headers={"X-Correlation-ID": corr_id} if corr_id else None,
            )
            if mresp.status_code != 200:
                raise HTTPException(status_code=400, detail="Menu not found")
            menu = mresp.json().get("items", [])
    except httpx.HTTPError:
        raise HTTPException(status_code=502, detail="Restaurant service unavailable")

    # Delivery must be same city as restaurant
    if rest.get("city") != payload.city:
        raise HTTPException(status_code=400, detail="Delivery city must match restaurant city")

    menu_by_id = {m["item_id"]: m for m in menu}

    # Validate and price
    subtotal = 0.0
    for line in payload.lines:
        mi = menu_by_id.get(line.item_id)
        if not mi or not mi.get("is_available", False):
            raise HTTPException(status_code=400, detail=f"Item {line.item_id} not available")
        price = float(mi.get("price", 0))
        subtotal += price * line.quantity

    tax = round(subtotal * TAX_RATE, 2)
    total = round(subtotal + tax + DELIVERY_FEE, 2)

    # Create order and items
    with SessionLocal() as db:
        order = Order(
            customer_id=payload.customer_id,
            restaurant_id=payload.restaurant_id,
            address_id=payload.address_id,
            order_status="PENDING",
            order_total=total,
            payment_status="INIT",
            restaurant_name=rest.get("name"),
            address_city=payload.city,
        )
        db.add(order)
        db.commit()
        db.refresh(order)

        for line in payload.lines:
            mi = menu_by_id[line.item_id]
            db.add(
                OrderItem(
                    order_id=order.order_id,
                    item_id=line.item_id,
                    quantity=line.quantity,
                    price=float(mi["price"]),
                )
            )
        db.commit()

        # Charge payment unless COD
        if payload.payment_method != "COD":
            pay_req = {
                "order_id": order.order_id,
                "amount": total,
                "method": payload.payment_method,
            }
            try:
                with httpx.Client(timeout=5.0) as client:
                    pr = client.post(
                        f"{PAYMENT_URL}/v1/payments/charge",
                        headers={
                            "Idempotency-Key": idempotency_key,
                            **({"X-Correlation-ID": corr_id} if corr_id else {}),
                        },
                        json=pay_req,
                    )
            except httpx.HTTPError:
                order.payment_status = "FAILED"
                db.commit()
                raise HTTPException(status_code=502, detail="Payment service unavailable")

            if pr.status_code != 200:
                # Payment service returns 400 on failure; map to user error
                order.payment_status = "FAILED"
                db.commit()
                # Bubble up payment error body if present
                try:
                    d = pr.json()
                    msg = d.get("detail") if isinstance(d, dict) else None
                except Exception:
                    msg = None
                raise HTTPException(status_code=400, detail=msg or "Payment failed")

            p = pr.json()
            order.payment_status = p.get("status", "FAILED")
        else:
            order.payment_status = "PENDING"

        # Confirm + kick off delivery + notify (best-effort background style)
        if order.payment_status == "SUCCESS" or payload.payment_method == "COD":
            order.order_status = "CONFIRMED"
            db.commit()

            # Assign driver (best-effort, ignore errors)
            try:
                with httpx.Client(timeout=5.0) as client:
                    client.post(
                        f"{DELIVERY_URL}/v1/deliveries/assign",
                        headers={"X-Correlation-ID": corr_id} if corr_id else None,
                        json={"order_id": order.order_id, "city": payload.city},
                    )
            except httpx.HTTPError:
                pass

            # Send notification (best-effort, ignore errors)
            try:
                with httpx.Client(timeout=3.0) as client:
                    client.post(
                        f"{NOTIF_URL}/v1/notifications",
                        headers={"X-Correlation-ID": corr_id} if corr_id else None,
                        json={"order_id": order.order_id, "type": "ORDER_CONFIRMED"},
                    )
            except httpx.HTTPError:
                pass
        else:
            # Non-COD and not SUCCESS -> already set to FAILED above
            db.commit()

        db.refresh(order)
        return OrderOut.model_validate(order)
