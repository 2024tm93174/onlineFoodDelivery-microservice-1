from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import select
from pydantic import BaseModel
from app.database import SessionLocal, engine
from app.models import Base, Restaurant, MenuItem

Base.metadata.create_all(bind=engine)
router = APIRouter(prefix="/restaurants/{restaurant_id}/menu", tags=["menu"])

class MenuItemOut(BaseModel):
    item_id: int
    name: str
    category: str
    price: float
    is_available: bool
    class Config:
        from_attributes = True

@router.get("", response_model=dict)
def list_menu(restaurant_id: int, page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200)):
    with SessionLocal() as db:
        if not db.get(Restaurant, restaurant_id):
            raise HTTPException(status_code=404, detail="Restaurant not found")
        stmt = select(MenuItem).where(MenuItem.restaurant_id==restaurant_id)
        total = db.scalar(stmt.count())
        items = db.execute(stmt.offset((page-1)*page_size).limit(page_size)).scalars().all()
        return {"items": [MenuItemOut.model_validate(i).model_dump() for i in items], "page": page, "page_size": page_size, "total": total}
