"""
Shafik's module: Operations & Basic Entities
Tables: announcements, complaints, drivers, buses, routes

Rules:
- snake_case for all table/column names
- UUID primary keys
- All timestamps are TIMESTAMPTZ stored in UTC
- Cross-owner references are plain UUID + index=True (NO explicit ForeignKey yet)
"""
import enum
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models import BaseModel


def utcnow() -> datetime:
    return datetime.now(timezone.utc)



# Enums

class ComplaintType(str, enum.Enum):
    complaint = "complaint"          # شكوى
    delay_report = "delay_report"    # بلاغ تأخير


class ComplaintStatus(str, enum.Enum):
    pending = "pending"
    in_review = "in_review"
    resolved = "resolved"
    rejected = "rejected"


class BusOwner(str, enum.Enum):
    university = "university"
    abu_el_hol = "abu_el_hol"



# announcements
class Announcement(BaseModel):
    __tablename__ = "announcements"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    is_urgent: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false", index=True
    )
    # Admin/user who published it (table owned by Mohamed Ali)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    published_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, index=True
    )



# drivers

class Driver(BaseModel):
    __tablename__ = "drivers"

    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    license_number: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    buses: Mapped[list["Bus"]] = relationship(back_populates="driver")



# buses

class Bus(BaseModel):
    __tablename__ = "buses"

    plate_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    bus_code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    owner: Mapped[BusOwner] = mapped_column(
        Enum(BusOwner, name="bus_owner"), nullable=False, index=True
    )
    # Same module (mine) so a real FK is safe here
    driver_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("drivers.id"), nullable=True, index=True
    )
    # Route assignment (routes table is also in this file)
    route_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    driver: Mapped[Optional["Driver"]] = relationship(back_populates="buses")
    route: Mapped[Optional["Route"]] = relationship(back_populates="buses")



# routes

class Route(BaseModel):
    __tablename__ = "routes"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )

    buses: Mapped[list["Bus"]] = relationship(back_populates="route")



# complaints

class Complaint(BaseModel):
    __tablename__ = "complaints"

    # Student who filed it (users table owned by Mohamed Ali)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, index=True
    )
    complaint_type: Mapped[ComplaintType] = mapped_column(
        Enum(ComplaintType, name="complaint_type"),
        nullable=False,
        default=ComplaintType.complaint,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    details: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus, name="complaint_status"),
        nullable=False,
        default=ComplaintStatus.pending,
        index=True,
    )
    # Optional context (same module, but kept optional)
    bus_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("buses.id"), nullable=True, index=True
    )
    route_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("routes.id"), nullable=True, index=True
    )
    # Admin reply / who handled it (users table owned by Mohamed Ali)
    admin_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True, index=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )



# TODO: INTEGRATION NOTES

# 1. في جدول announcements:
#    - ربط الحقل created_by بـ ForeignKey لجدول users.id عند (محمد علي)
#
# 2. في جدول complaints:
#    - ربط الحقل user_id بـ ForeignKey لجدول users.id عند (محمد علي)
#    - ربط الحقل resolved_by بـ ForeignKey لجدول users.id عند (محمد علي)
#    - إضافة relationship لـ User لو محتاجينها (complaint.user)
#    - (bus_id و route_id متربطين  بجداول buses و routes عندي)
#
# 3. في جدول buses:
#    - driver_id و route_idمتربطين اً (drivers / routes في نفس الملف)
#    - ممكن لاحقاً يتعمل many-to-many بين buses و routes
#      (جدول وسيط) لو الباص الواحد بيخدم أكتر من خط
#
# 4. جداول عند (أنا / محمد علي) هتحتاج تربط بجداول الملف ده:
#    - subscriptions (محمد علي): ربط bus_id بـ buses.id و route_id بـ routes.id
#    - requests (محمد علي): ربط route_id الحالي/الجديد بـ routes.id
#    - stations (أنا): ربط route_id بـ routes.id
#    - trip_locations / boardings / sos_alerts (أنا): ربط bus_id بـ buses.id
#
# 5. حقول id و created_at و updated_at يوفرها BaseModel المشترك.
