import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.common.models import BaseModel

class ReportExport(BaseModel):
    """جدول متابعة طلبات تصدير ملفات التقارير (PDF / Excel / CSV)"""
    __tablename__ = "report_exports"

    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="معرف المسؤول أو المشرف الذي طلب التقرير"
    )
    report_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="نوع التقرير: SUBSCRIPTIONS, ATTENDANCE, FLEET_COSTS, VIOLATIONS"
    )
    file_format: Mapped[str] = mapped_column(
        String(10),
        default="PDF",
        nullable=False,
        comment="صيغة الملف: PDF, XLSX, CSV"
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="PENDING",
        nullable=False,
        index=True,
        comment="حالة الإنشاء: PENDING, PROCESSING, COMPLETED, FAILED"
    )
    file_url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="رابط تحميل الملف بعد اكتمال إنشائه"
    )
    parameters: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="فلاتر التقرير كالتاريخ وخط السير بصيغة JSONB"
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="توقيت اكتمال المعالجة وتجهيز الرابط"
    )

class AuditLog(BaseModel):
    """جدول سجل التدقيق والرقابة الإدارية لجميع العمليات الحساسة"""
    __tablename__ = "audit_logs"

    actor_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
        comment="معرف المستخدم الذي نفذ العملية الحساسة"
    )
    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="نوع العملية: UPDATE_SUBSCRIPTION, RESOLVE_SOS, EXPORT_REPORT"
    )
    entity_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="اسم الجدول أو الكيان المتأثر: Subscription, Bus, SOSAlert"
    )
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        comment="معرف الكيان المتأثر"
    )
    changes: Mapped[Optional[dict]] = mapped_column(
        JSONB,
        nullable=True,
        comment="البيانات قبل التعديل وبعده لتتبع الفروق"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="عنوان IP الخاص بالمنفذ"
    )

# ==========================================
# TODO: INTEGRATION NOTES (عند اكتمال موديول auth)
# ==========================================
# 1. في جدول ReportExport:
#    - تعديل requested_by ليصبح ForeignKey("users.id", ondelete="RESTRICT")
#    - إضافة relationship("User", backref="report_exports")
#
# 2. في جدول AuditLog:
#    - تعديل actor_id ليصبح ForeignKey("users.id", ondelete="RESTRICT")
#    - إضافة relationship("User", backref="audit_logs")
