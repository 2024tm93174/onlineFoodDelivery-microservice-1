from fastapi import APIRouter, Query, HTTPException
from sqlalchemy import select, func
from pydantic import BaseModel
from app.database import SessionLocal, engine
from app.models import Base, Restaurant

# IMPORTANT:
# Don't call Base.metadata.create_all(bind=engine) at import time.
# Do this in app/main.py inside a FastAPI startup event to avoid DB race conditions.

router = APIRouter(prefix="/v1/restaurants", tags=["restaurants"])


# ---------- Pydantic schema ----------

class RestaurantOut(BaseModel):
    restaurant_id: int
    name: str
    cuisine: str
    city: str
    rating: float
    is_open: bool


    # Pydantic v2 config
    model_config = {"from_attributes": True}


# ---------- Endpoints ----------
@router.get("", response_model=dict)
def list_restaurants(
    city: str | None = None,
    cuisine: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """
    Paginated list of restaurants, optionally filtered by city and/or cuisine.

    SQLAlchemy 2.x: `Select.count()` was removed.
    Use `select(func.count()).select_from(stmt.subquery())` for an exact total that
    mirrors the same filters as the main query.
    """
    with SessionLocal() as db:
        # Build the main statement with optional filters
        stmt = select(Restaurant)
        if city:
            stmt = stmt.where(Restaurant.city == city)
        if cuisine:
            stmt = stmt.where(Restaurant.cuisine == cuisine)

        # Accurate total using the same filters
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = db.scalar(count_stmt) or 0

        # Page of rows (order by primary key for stable pagination)
        items = (
            db.execute(
                stmt.order_by(Restaurant.restaurant_id)
                    .offset((page - 1) * page_size)
                    .limit(page_size)
            )
            .scalars()
            .all()
        )

        return {
            "items": [RestaurantOut.model_validate(i).model_dump() for i in items],
            "page": page,
            "page_size": page_size,
            "total": total,
        }


@router.get("/{restaurant_id}", response_model=RestaurantOut)
def get_restaurant(restaurant_id: int):
    with SessionLocal() as db:
        r = db.get(Restaurant, restaurant_id)
        if not r:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        return RestaurantOut.model_validate(r)
