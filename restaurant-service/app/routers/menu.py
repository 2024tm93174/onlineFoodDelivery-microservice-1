from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import select, func
from pydantic import BaseModel
from app.database import SessionLocal
from app.models import Restaurant, MenuItem

# IMPORTANT:
# Do NOT call Base.metadata.create_all() here; do it in app/main.py at startup.

# If your main.py does NOT add a global "/v1" prefix, keep /v1 here.
# If your main.py DOES include_router(..., prefix="/v1"), then change the
# prefix below to "/restaurants/{restaurant_id}/menu".
router = APIRouter(prefix="/v1/restaurants/{restaurant_id}/menu", tags=["menu"])

class MenuItemOut(BaseModel):
    item_id: int
    name: str
    category: str | None = None
    price: float
    is_available: bool

    # Pydantic v2 style
    model_config = {"from_attributes": True}

@router.get("", response_model=dict)
def list_menu(
    restaurant_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    with SessionLocal() as db:
        # 404 if restaurant doesn't exist
        if not db.get(Restaurant, restaurant_id):
            raise HTTPException(status_code=404, detail="Restaurant not found")

        # total count (SQLAlchemy 2.x safe)
        total = db.scalar(
            select(func.count(MenuItem.item_id)).where(MenuItem.restaurant_id == restaurant_id)
        ) or 0

        # page of items
        items = (
            db.execute(
                select(MenuItem)
                .where(MenuItem.restaurant_id == restaurant_id)
                .order_by(MenuItem.item_id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            .scalars()
            .all()
        )

        return {
            "items": [MenuItemOut.model_validate(i).model_dump() for i in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        }


