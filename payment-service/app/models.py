from datetime import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Payment(Base):
    __tablename__ = "payments"

    payment_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, index=True)
    amount: Mapped[float] = mapped_column(Float)
    method: Mapped[str] = mapped_column(String(20))  # CARD | UPI | WALLET | COD
    status: Mapped[str] = mapped_column(String(20))  # SUCCESS | FAILED | PENDING
    reference: Mapped[str] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64))
    request_hash: Mapped[str] = mapped_column(String(64))
    response_body: Mapped[str] = mapped_column(String(4096))  # JSON string

    __table_args__ = (
        UniqueConstraint("key", "request_hash", name="uq_key_hash"),
    )

