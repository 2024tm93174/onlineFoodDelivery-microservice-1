from sqlalchemy import String, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase): pass

class Customer(Base):
    __tablename__ = "customers"
    customer_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    created_at: Mapped = mapped_column(DateTime, server_default=func.now())
    addresses: Mapped[list["Address"]] = relationship("Address", back_populates="customer", cascade="all, delete-orphan")

class Address(Base):
    __tablename__ = "addresses"
    address_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.customer_id", ondelete="CASCADE"))
    line1: Mapped[str] = mapped_column(String(255))
    area: Mapped[str] = mapped_column(String(120))
    city: Mapped[str] = mapped_column(String(120), index=True)
    pincode: Mapped[str] = mapped_column(String(10))
    created_at: Mapped = mapped_column(DateTime, server_default=func.now())
    customer: Mapped["Customer"] = relationship("Customer", back_populates="addresses")
