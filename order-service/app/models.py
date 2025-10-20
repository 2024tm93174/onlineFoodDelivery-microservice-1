# order-service/app/models.py
from datetime import datetime
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, DateTime, Identity

Base = declarative_base()

# Explicit Identity() keeps Postgres sequences well-defined.
class Customer(Base):
    __tablename__ = "customers"
    customer_id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)
    name: Mapped[str]        = mapped_column(String(100), nullable=False)
    email: Mapped[str]       = mapped_column(String(200), nullable=False, unique=True)
    phone: Mapped[str]       = mapped_column(String(40), nullable=False)

class Restaurant(Base):
    __tablename__ = "restaurants"
    restaurant_id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)
    name: Mapped[str]          = mapped_column(String(120), nullable=False)
    cuisine: Mapped[str]       = mapped_column(String(60), nullable=False)
    city: Mapped[str]          = mapped_column(String(80), nullable=False)
    rating: Mapped[float]      = mapped_column(Float, nullable=False, default=0.0)
    is_open: Mapped[bool]      = mapped_column(Boolean, nullable=False, default=True)

class MenuItem(Base):
    __tablename__ = "menu_items"
    item_id: Mapped[int]       = mapped_column(Integer, Identity(always=False), primary_key=True)
    restaurant_id: Mapped[int] = mapped_column(ForeignKey("restaurants.restaurant_id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str]          = mapped_column(String(120), nullable=False)
    category: Mapped[str]      = mapped_column(String(60), nullable=False)
    price: Mapped[float]       = mapped_column(Float, nullable=False)
    is_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

class Address(Base):
    __tablename__ = "addresses"
    address_id: Mapped[int] = mapped_column(Integer, Identity(always=False), primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id", ondelete="CASCADE"), nullable=False)
    line1: Mapped[str]       = mapped_column(String(200), nullable=False)
    city: Mapped[str]        = mapped_column(String(80), nullable=False)
    pincode: Mapped[str]     = mapped_column(String(20), nullable=False)

class Order(Base):
    __tablename__ = "orders"
    order_id: Mapped[int]       = mapped_column(Integer, Identity(always=False), primary_key=True)
    customer_id: Mapped[int]    = mapped_column(ForeignKey("customers.customer_id"), nullable=False)
    restaurant_id: Mapped[int]  = mapped_column(ForeignKey("restaurants.restaurant_id"), nullable=False)
    address_id: Mapped[int]     = mapped_column(ForeignKey("addresses.address_id"), nullable=False)
    order_status: Mapped[str]   = mapped_column(String(40), nullable=False, default="PENDING")
    order_total: Mapped[float]  = mapped_column(Float, nullable=False, default=0.0)
    payment_status: Mapped[str] = mapped_column(String(40), nullable=False, default="INIT")
    restaurant_name: Mapped[str] = mapped_column(String(120), nullable=True)
    address_city: Mapped[str]    = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int]        = mapped_column(Integer, Identity(always=False), primary_key=True)
    order_id: Mapped[int]  = mapped_column(ForeignKey("orders.order_id", ondelete="CASCADE"), nullable=False, index=True)
    item_id: Mapped[int]   = mapped_column(Integer, nullable=False)
    quantity: Mapped[int]  = mapped_column(Integer, nullable=False)
    price: Mapped[float]   = mapped_column(Float, nullable=False)

    order: Mapped["Order"] = relationship("Order", back_populates="items")

