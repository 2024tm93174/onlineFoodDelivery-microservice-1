
import os, math
import pandas as pd
from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models import Base, Payment


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
payments_csv = os.path.join(DATA_DIR, "payments.csv")

def seed():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE payments RESTART IDENTITY CASCADE"))
        conn.execute(text("TRUNCATE TABLE idempotency_keys RESTART IDENTITY CASCADE"))
    with SessionLocal() as db:
        df = pd.read_csv(payments_csv)
        for _, r in df.iterrows():
            db.add(Payment(
                payment_id=int(r["payment_id"]),
                order_id=int(r["order_id"]),
                amount=float(r["amount"]),
                method=str(r["method"]),
                status=str(r["status"]),
                reference=str(r["reference"]),
                created_at=parse_dt(r.get("created_at")),
            ))
        db.commit()
    print("payment-service: seeded payments.")

if __name__ == "__main__":
    seed()
