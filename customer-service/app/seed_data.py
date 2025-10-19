
import os, math
import pandas as pd
from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models import Base, Customer, Address


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
customers_csv = os.path.join(DATA_DIR, "customers.csv")
addresses_csv = os.path.join(DATA_DIR, "addresses.csv")

def seed():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        # truncate (safe for reseed)
        conn.execute(text("TRUNCATE TABLE addresses RESTART IDENTITY CASCADE"))
        conn.execute(text("TRUNCATE TABLE customers RESTART IDENTITY CASCADE"))
    with SessionLocal() as db:
        # customers
        dfc = pd.read_csv(customers_csv)
        for _, r in dfc.iterrows():
            db.add(Customer(
                customer_id=int(r["customer_id"]),
                name=str(r["name"]),
                email=str(r["email"]),
                phone=str(r["phone"]),
                created_at=parse_dt(r.get("created_at"))
            ))
        db.commit()
        # addresses
        dfa = pd.read_csv(addresses_csv)
        for _, r in dfa.iterrows():
            db.add(Address(
                address_id=int(r["address_id"]),
                customer_id=int(r["customer_id"]),
                line1=str(r["line1"]),
                area=str(r["area"]),
                city=str(r["city"]),
                pincode=str(r["pincode"]),
                created_at=parse_dt(r.get("created_at"))
            ))
        db.commit()
    print("customer-service: seeded customers & addresses.")

if __name__ == "__main__":
    seed()
