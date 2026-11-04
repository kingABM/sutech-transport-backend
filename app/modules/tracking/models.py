import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, Boolean, ForeignKey, Index, DateTime, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from geoalchemy2 import Geometry

from app.common.models import BaseModel

class Station(BaseModel):
    """جدول المحطات ونقاط التوقف الجغرافية"""
    __tablename__ = "stations"

    name_ar: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        comment="اسم المحطة باللغة العربية"
    )
    name_en: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        comment="اسم المحطة باللغة الإنجليزية"
    )

    # النقطة الجغرافية للمحطة بنظام WGS 84 (SRID 4326)
    location = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
        comment="إحداثيات المحطة الجغرافية (خط الطول ودائرة العرض)"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="حالة تفعيل المحطة"
    )

    # فهرس جغرافي مكاني لتسريع حساب أقرب محطة للطلاب
    __table_args__ = (
        Index("ix_stations_location_gist", location, postgresql_using="gist"),
    )

class TripLocation(BaseModel):
    """سجل التتبع الحي لمواقع الحافلات والسرعة"""
    __tablename__ = "trip_locations"

    bus_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="معرف الحافلة التابع لموديول الأسطول"
    )
    trip_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="معرف الرحلة الحالية"
    )

    # موقع الباص اللحظي
    coordinates = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
        comment="الإحداثيات اللحظية للحافلة"
    )
    speed: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="السرعة اللحظية بالكيلومتر/ساعة"
    )
    heading: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="زاوية اتجاه الباص (من 0 إلى 360 درجة)"
    )
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="توقيت التقاط الإحداثية من جهاز التتبع"
    )

    # فهرس مكاني وزمني لتسريع استرجاع مسار الرحلة على الخريطة
    __table_args__ = (
        Index("ix_trip_locations_coords_gist", coordinates, postgresql_using="gist"),
    )

class SOSAlert(BaseModel):
    """جدول بلاغات الطوارئ وزر الاستغاثة (SOS)"""
    __tablename__ = "sos_alerts"

    bus_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="معرف الحافلة المستغيثة"
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="معرف السائق مطلق البلاغ"
    )
    trip_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="معرف الرحلة المرتبطة بالحادث"
    )
    alert_type: Mapped[str] = mapped_column(
        String(50),
        default="SOS",
        nullable=False,
        comment="نوع البلاغ: SOS، عطل ميكانيكي، حادث، تأخير حاد"
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="OPEN",
        nullable=False,
        index=True,
        comment="حالة البلاغ: OPEN, IN_PROGRESS, RESOLVED"
    )

    # موقع إطلاق البلاغ جغرافياً
    location = mapped_column(
        Geometry(geometry_type="POINT", srid=4326),
        nullable=False,
        comment="الموقع الجغرافي الدقيق للباص لحظة إطلاق الطوارئ"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="وصف إضافي من السائق أو الملاحظات"
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="توقيت إغلاق البلاغ وحل المشكلة"
    )
    resolved_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="معرف الأدمن الذي قام بالتعامل مع البلاغ وإغلاقه"
    )

    __table_args__ = (
        Index("ix_sos_alerts_location_gist", location, postgresql_using="gist"),
    )


# ==========================================
# TODO: INTEGRATION NOTES (عند اكتمال موديولي fleet و auth)
# ==========================================
# 1. في جدول TripLocation:
#    - ربط bus_id بـ ForeignKey("buses.id", ondelete="CASCADE")
#    - ربط trip_id بـ ForeignKey("trips.id", ondelete="SET NULL")
#
# 2. في جدول SOSAlert:
#    - ربط bus_id بـ ForeignKey("buses.id", ondelete="CASCADE")
#    - ربط driver_id بـ ForeignKey("users.id", ondelete="RESTRICT")
#    - ربط trip_id بـ ForeignKey("trips.id", ondelete="SET NULL")
#    - ربط resolved_by بـ ForeignKey("users.id", ondelete="SET NULL")
