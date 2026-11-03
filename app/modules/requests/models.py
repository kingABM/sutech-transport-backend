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


class RequestType(str, enum.Enum):
    refund = "refund"
    line_transfer = "line_transfer"
    lost_card = "lost_card"


class RequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    cancelled = "cancelled"


class Request(BaseModel):
    __tablename__ = "requests"
    __table_args__ = (
        CheckConstraint("type <> 'line_transfer' OR target_route_id IS NOT NULL", name="ck_req_transfer_target"),
        CheckConstraint("refund_piastres IS NULL OR refund_piastres > 0", name="ck_req_refund_pos"),
        Index("ix_requests_status_type", "status", "type"),
    )

    requester_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)  # TODO FK users.id
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)  # TODO FK subscriptions.id
    type: Mapped[RequestType] = mapped_column(pg_enum(RequestType, "request_type"))
    status: Mapped[RequestStatus] = mapped_column(
        pg_enum(RequestStatus, "request_status"), default=RequestStatus.pending
    )
    reason: Mapped[str | None] = mapped_column(Text)
    target_route_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)  # TODO FK routes.id (شفيق / fleet)
    refund_piastres: Mapped[int | None] = mapped_column(BigInteger)
    decided_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)  # TODO FK users.id
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decision_note: Mapped[str | None] = mapped_column(Text)


# ==========================================
# TODO: INTEGRATION NOTES
# ==========================================
# 1. في جدول requests:
#    - requester_id, decided_by -> ForeignKey("users.id")        (auth - محمد علي)
#    - subscription_id          -> ForeignKey("subscriptions.id") (subscriptions - محمد علي)
#    - target_route_id          -> ForeignKey("routes.id")        (fleet - شفيق)
# 2. relationship (اختياري): Request.subscription, Request.requester.
