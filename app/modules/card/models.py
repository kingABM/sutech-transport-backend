import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Boolean, ForeignKey, DateTime, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models import BaseModel

class DigitalCard(BaseModel):
    """جدول الكارنيه الرقمي للطالب والمفاتيح السرية للتشفير"""
    __tablename__ = "digital_cards"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        unique=True,
        index=True,
        comment="معرف الطالب صاحب الكارنيه (من موديول المستخدمين)"
    )
    card_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="رقم الكارنيه الرقمي الفريد المعروض للطالب"
    )
    totp_secret: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="المفتاح السري المشفر لتوليد كود الـ QR المتغير كل 30-60 ثانية"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="حالة تفعيل الكارنيه (إيقاف في حال تجميد الاشتراك)"
    )
    last_scanned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="توقيت آخر عملية مسح ناجحة للكارنيه"
    )

class Boarding(BaseModel):
    """سجل صعود الحافلات وعمليات فحص الكارنيه لمنع التكرار والتزوير"""
    __tablename__ = "boardings"

    card_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("digital_cards.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="معرف الكارنيه الممسوح"
    )
    bus_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="معرف الحافلة التي تم الصعود إليها"
    )
    station_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="المحطة التي تم فيها الصعود"
    )
    driver_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="معرف السائق أو المشرف الذي مسح الكود بجهازه"
    )
    scanned_code_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        comment="هاش كود الـ QR المستخدم لمنع إعادة استخدامه (Replay Attack)"
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="ACCEPTED",
        nullable=False,
        comment="نتيجة الفحص: ACCEPTED, EXPIRED, REJECTED, DUPLICATE"
    )
    scanned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="توقيت مسح الكود والتحقق منه"
    )


# ==========================================
# TODO: INTEGRATION NOTES (عند اكتمال موديولي fleet و auth)
# ==========================================
# 1. في جدول DigitalCard:
#    - تعديل user_id ليصبح ForeignKey("users.id", ondelete="CASCADE")
#    - إضافة relationship("User", back_populates="digital_card")
#
# 2. في جدول Boarding:
#    - ربط bus_id بـ ForeignKey("buses.id", ondelete="CASCADE")
#    - ربط driver_id بـ ForeignKey("users.id", ondelete="RESTRICT")
#    - ربط station_id بـ ForeignKey("stations.id", ondelete="SET NULL")
