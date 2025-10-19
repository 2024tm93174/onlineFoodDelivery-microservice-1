from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Restaurant(Base):
    __tablename__ = "restaurants"

    restaurant_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    cuisine: Mapped[str] = mapped_column(String(120), index=True)
    city: Mapped[str] = mapped_column(String(120), index=True)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    is_open: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relationship
    menu_items: Mapped[list["MenuItem"]] = relationship(
        "MenuItem",
        back_populates="restaurant",
        cascade="all, delete-orphan"
    )


class MenuItem(Base):
    __tablename__ = "menu_items"

    item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    restaurant_id: Mapped[int] = mapped_column(
        ForeignKey("restaurants.restaurant_id", ondelete="CASCADE"),
        index=True
    )
    name: Mapped[str] = mapped_column(String(200), index=True)
    category: Mapped[str] = mapped_column(String(120), index=True)
    price: Mapped[float] = mapped_column(Float)
    is_available: Mapped[bool] = mapped_column(Boolean, default=True)

    # Relationship
    restaurant: Mapped["Restaurant"] = relationship("Restaurant", back_populates="menu_items")

