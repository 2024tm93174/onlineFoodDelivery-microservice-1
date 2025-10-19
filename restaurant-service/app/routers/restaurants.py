from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import select
from pydantic import BaseModel
from app.database import SessionLocal, engine
from app.models import Base, Restaurant, MenuItem

Base.metadata.create_all(bind=engine)
router = APIRouter(prefix="/restaurants", tags=["restaurants"])

class RestaurantOut(BaseModel):
    restaurant_id: int
    name: str
    cuisine: str
    city: str
    rating: float
    is_open: bool
    class Config:
        from_attributes = True

@router.get("", response_model=dict)
def list_restaurants(city: str | None = None, cuisine: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100)):
    with SessionLocal() as db:
        stmt = select(Restaurant)
        if city:
            stmt = stmt.where(Restaurant.city==city)
        if cuisine:
            stmt = stmt.where(Restaurant.cuisine==cuisine)
        total = db.scalar(stmt.count())
        items = db.execute(stmt.offset((page-1)*page_size).limit(page_size)).scalars().all()
        return {"items": [RestaurantOut.model_validate(i).model_dump() for i in items], "page": page, "page_size": page_size, "total": total}

@router.get("/{restaurant_id}", response_model=RestaurantOut)
def get_restaurant(restaurant_id: int):
    with SessionLocal() as db:
        r = db.get(Restaurant, restaurant_id)
        if not r:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        return RestaurantOut.model_validate(r)
