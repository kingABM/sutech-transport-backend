import enum
import uuid
from datetime import date, datetime

import sqlalchemy as sa
from sqlalchemy import BigInteger, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models import BaseModel  # gives id (UUID), created_at, updated_at


def pg_enum(e, name):
    return sa.Enum(e, name=name, values_callable=lambda x: [m.value for m in x])


class PaymentMethod(str, enum.Enum):
    instapay = "instapay"
    fawry = "fawry"


class PaymentStatus(str, enum.Enum):
    pending = "pending"
    under_review = "under_review"
    confirmed = "confirmed"
    rejected = "rejected"


class Payment(BaseModel):
    __tablename__ = "payments"
    __table_args__ = (
        CheckConstraint("amount_piastres > 0", name="ck_payments_amount_pos"),
        Index(
            "uq_payment_method_ref", "method", "external_reference", unique=True,
            postgresql_where=sa.text("external_reference IS NOT NULL"),
        ),
    )

    subscription_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)  # TODO FK subscriptions.id
    payer_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)  # TODO FK users.id
    amount_piastres: Mapped[int] = mapped_column(BigInteger)  # 1,500 EGP = 150000
    method: Mapped[PaymentMethod] = mapped_column(pg_enum(PaymentMethod, "payment_method"))
    status: Mapped[PaymentStatus] = mapped_column(
        pg_enum(PaymentStatus, "payment_status"), default=PaymentStatus.pending, index=True
    )
    external_reference: Mapped[str | None] = mapped_column(String(100))
    receipt_url: Mapped[str | None] = mapped_column(Text)
    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)  # TODO FK users.id
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class IdempotencyKey(BaseModel):
    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(100), unique=True)
    request_hash: Mapped[str] = mapped_column(String(64))
    payment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("payments.id", ondelete="SET NULL"))
    response_body: Mapped[dict | None] = mapped_column(JSONB)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


# ==========================================
# TODO: INTEGRATION NOTES
# ==========================================
# 1. في جدول payments:
#    - subscription_id -> ForeignKey("subscriptions.id")  (موديول subscriptions عند محمد علي)
#    - payer_user_id, reviewed_by -> ForeignKey("users.id") (موديول auth عند محمد علي)
# 2. idempotency_keys.payment_id -> ForeignKey("payments.id") موجود فعلاً (نفس الملف).
# 3. relationship (اختياري): Payment.subscription.
