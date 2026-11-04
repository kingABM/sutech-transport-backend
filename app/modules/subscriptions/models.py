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


class SubscriptionStatus(str, enum.Enum):
    reserved = "reserved"
    active = "active"
    expired = "expired"
    cancelled = "cancelled"
    refunded = "refunded"


class Term(BaseModel):
    __tablename__ = "terms"
    __table_args__ = (
        CheckConstraint("ends_on > starts_on", name="ck_terms_dates"),
        CheckConstraint("booking_closes_at > booking_opens_at", name="ck_terms_booking"),
        Index("uq_terms_one_current", "is_current", unique=True, postgresql_where=sa.text("is_current")),
    )

    name: Mapped[str] = mapped_column(String(80))
    academic_year: Mapped[str] = mapped_column(String(9))
    starts_on: Mapped[date] = mapped_column(Date)
    ends_on: Mapped[date] = mapped_column(Date)
    booking_opens_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    booking_closes_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    price_piastres: Mapped[int] = mapped_column(BigInteger)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False, server_default=sa.false())


class Subscription(BaseModel):
    __tablename__ = "subscriptions"
    __table_args__ = (
        Index(
            "uq_sub_student_term_live", "student_id", "term_id", unique=True,
            postgresql_where=sa.text("status IN ('reserved','active')"),
        ),
        Index("ix_sub_route_status", "route_id", "status"),
        Index("ix_sub_reserved_expiry", "expires_at", postgresql_where=sa.text("status = 'reserved'")),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)  # TODO FK users.id (محمد علي / auth)
    term_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("terms.id"))
    route_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))  # TODO FK routes.id (شفيق / fleet)
    station_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)  # TODO FK stations.id (عبد الله / tracking)
    status: Mapped[SubscriptionStatus] = mapped_column(
        pg_enum(SubscriptionStatus, "subscription_status"), default=SubscriptionStatus.reserved
    )
    reserved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=sa.func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))  # reserved_at + 24h
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# ==========================================
# TODO: INTEGRATION NOTES
# ==========================================
# 1. في جدول subscriptions:
#    - student_id  -> ForeignKey("users.id")     عند محمد علي (auth)
#    - route_id    -> ForeignKey("routes.id")    عند شفيق (fleet)
#    - station_id  -> ForeignKey("stations.id")  عند عبد الله (tracking)
#    - term_id     -> ForeignKey("terms.id") موجود فعلاً (نفس الملف)
# 2. فحص السعة في reserve (service.py): SELECT ... FOR UPDATE على صف الخط، مش هنا.
# 3. relationship (اختياري): Subscription.term, Subscription.payments.
