from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, func, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase): pass

class Order(Base):
    __tablename__ = "orders"
    order_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(Integer, index=True)
    restaurant_id: Mapped[int] = mapped_column(Integer, index=True)
    address_id: Mapped[int] = mapped_column(Integer)
    order_status: Mapped[str] = mapped_column(String(20), default="PENDING")  # PENDING|CONFIRMED|CANCELLED
    order_total: Mapped[float] = mapped_column(Float, default=0.0)
    payment_status: Mapped[str] = mapped_column(String(20), default="INIT")   # INIT|PENDING|SUCCESS|FAILED
    created_at: Mapped = mapped_column(DateTime, server_default=func.now())
    # replicated read fields (decoupling; for statements)
    restaurant_name: Mapped[str] = mapped_column(String(200))
    address_city: Mapped[str] = mapped_column(String(120))
    items: Mapped[list["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

class OrderItem(Base):
    __tablename__ = "order_items"
    order_item_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.order_id", ondelete="CASCADE"))
    item_id: Mapped[int] = mapped_column(Integer)
    quantity: Mapped[int] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Float)
    order: Mapped["Order"] = relationship("Order", back_populates="items")
