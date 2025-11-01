
import os, math
import pandas as pd
from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models import Base, Order, OrderItem


import os, csv, math
from datetime import datetime
from sqlalchemy import text
from sqlalchemy.orm import Session

def parse_dt(val: str):
    if not val or (isinstance(val, float) and math.isnan(val)):
        return None
    val = str(val).strip()
    # Try multiple formats
    for fmt in ("%d/%m/%y %H:%M", "%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            continue
    # Fallback: try to parse date-only
    for fmt in ("%d/%m/%y", "%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(val, fmt)
        except ValueError:
            continue
    return None


DATA_DIR = os.getenv("DATA_DIR", "/seed/data")
orders_csv = os.path.join(DATA_DIR, "orders.csv")
order_items_csv = os.path.join(DATA_DIR, "order_items.csv")
# To populate replicated fields:
restaurants_csv = os.path.join(DATA_DIR, "restaurants.csv")
addresses_csv = os.path.join(DATA_DIR, "addresses.csv")

def seed():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE order_items RESTART IDENTITY CASCADE"))
        conn.execute(text("TRUNCATE TABLE orders RESTART IDENTITY CASCADE"))
    # Load aux maps for replicated fields
    dfr = pd.read_csv(restaurants_csv)[["restaurant_id","name","city"]].set_index("restaurant_id").to_dict(orient="index")
    dfa = pd.read_csv(addresses_csv)[["address_id","city"]].set_index("address_id")["city"].to_dict()

    with SessionLocal() as db:
        # orders
        dfo = pd.read_csv(orders_csv)
        for _, r in dfo.iterrows():
            rid = int(r["restaurant_id"])
            aid = int(r["address_id"])
            rest = dfr.get(rid, {})
            db.add(Order(
                order_id=int(r["order_id"]),
                customer_id=int(r["customer_id"]),
                restaurant_id=rid,
                address_id=aid,
                order_status=str(r["order_status"]),
                order_total=float(r["order_total"]),
                payment_status=str(r["payment_status"]),
                created_at=parse_dt(r.get("created_at")),
                restaurant_name=str(rest.get("name", "")),
                address_city=str(dfa.get(aid, "")),
            ))
        db.commit()
        # order_items
        dfi = pd.read_csv(order_items_csv)
        for _, r in dfi.iterrows():
            db.add(OrderItem(
                id = int(r["order_item_id"]),
                order_id=int(r["order_id"]),
                item_id=int(r["item_id"]),
                quantity=int(r["quantity"]),
                price=float(r["price"]),
            ))
        db.commit()
    print("order-service: seeded orders & order_items.")

if __name__ == "__main__":
    seed()
