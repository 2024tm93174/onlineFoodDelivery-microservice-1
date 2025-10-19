
import os, math
import pandas as pd
from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models import Base, Driver, Delivery


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
drivers_csv = os.path.join(DATA_DIR, "drivers.csv")
deliveries_csv = os.path.join(DATA_DIR, "deliveries.csv")

def seed():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE deliveries RESTART IDENTITY CASCADE"))
        conn.execute(text("TRUNCATE TABLE drivers RESTART IDENTITY CASCADE"))
    with SessionLocal() as db:
        # drivers
        dfd = pd.read_csv(drivers_csv)
        for _, r in dfd.iterrows():
            db.add(Driver(
                driver_id=int(r["driver_id"]),
                name=str(r["name"]),
                phone=str(r["phone"]),
                vehicle_type=str(r["vehicle_type"]),
                is_active=bool(r["is_active"]),
            ))
        db.commit()
        # deliveries
        dfl = pd.read_csv(deliveries_csv)
        for _, r in dfl.iterrows():
            db.add(Delivery(
                delivery_id=int(r["delivery_id"]),
                order_id=int(r["order_id"]),
                driver_id=int(r["driver_id"]),
                status=str(r["status"]),
                assigned_at=parse_dt(r.get("assigned_at")),
                picked_at=parse_dt(r.get("picked_at")),
                delivered_at=parse_dt(r.get("delivered_at")),
            ))
        db.commit()
    print("delivery-service: seeded drivers & deliveries.")

if __name__ == "__main__":
    seed()
