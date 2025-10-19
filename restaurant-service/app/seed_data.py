
import os, math
import pandas as pd
from sqlalchemy import text
from app.database import engine, SessionLocal
from app.models import Base, Restaurant, MenuItem


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
restaurants_csv = os.path.join(DATA_DIR, "restaurants.csv")
menu_items_csv = os.path.join(DATA_DIR, "menu_items.csv")

def seed():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE menu_items RESTART IDENTITY CASCADE"))
        conn.execute(text("TRUNCATE TABLE restaurants RESTART IDENTITY CASCADE"))
    with SessionLocal() as db:
        # restaurants
        dfr = pd.read_csv(restaurants_csv)
        for _, r in dfr.iterrows():
            db.add(Restaurant(
                restaurant_id=int(r["restaurant_id"]),
                name=str(r["name"]),
                cuisine=str(r["cuisine"]),
                city=str(r["city"]),
                rating=float(r["rating"]),
                is_open=bool(r["is_open"]),
                created_at=parse_dt(r.get("created_at"))
            ))
        db.commit()
        # menu_items
        dfm = pd.read_csv(menu_items_csv)
        for _, r in dfm.iterrows():
            db.add(MenuItem(
                item_id=int(r["item_id"]),
                restaurant_id=int(r["restaurant_id"]),
                name=str(r["name"]),
                category=str(r["category"]),
                price=float(r["price"]),
                is_available=bool(r["is_available"]),
            ))
        db.commit()
    print("restaurant-service: seeded restaurants & menu_items.")

if __name__ == "__main__":
    seed()
