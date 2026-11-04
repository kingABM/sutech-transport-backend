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


class UserRole(str, enum.Enum):
    student = "student"
    parent = "parent"
    driver = "driver"
    supervisor = "supervisor"
    admin = "admin"


class OTPPurpose(str, enum.Enum):
    login = "login"
    register = "register"
    phone_change = "phone_change"


class User(BaseModel):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role <> 'student' OR university_id IS NOT NULL", name="ck_users_student_uid"),
    )

    full_name: Mapped[str] = mapped_column(String(150))
    university_id: Mapped[str | None] = mapped_column(String(20), unique=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True)
    role: Mapped[UserRole] = mapped_column(pg_enum(UserRole, "user_role"), index=True)
    language: Mapped[str] = mapped_column(String(2), default="ar", server_default="ar")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sa.true())
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OTPCode(BaseModel):
    __tablename__ = "otp_codes"
    __table_args__ = (Index("ix_otp_phone_created", "phone", "created_at"),)

    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    phone: Mapped[str] = mapped_column(String(20))
    code_hash: Mapped[str] = mapped_column(String(128))  # hash only, never the raw OTP
    purpose: Mapped[OTPPurpose] = mapped_column(pg_enum(OTPPurpose, "otp_purpose"), default=OTPPurpose.login)
    attempts: Mapped[int] = mapped_column(SmallInteger, default=0, server_default="0")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Guardian(BaseModel):
    __tablename__ = "guardians"
    __table_args__ = (
        UniqueConstraint("guardian_user_id", "student_user_id", name="uq_guardian_student"),
        CheckConstraint("guardian_user_id <> student_user_id", name="ck_guardian_not_self"),
    )

    guardian_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    student_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    relationship: Mapped[str] = mapped_column(String(30), default="parent", server_default="parent")


# ==========================================
# TODO: INTEGRATION NOTES
# ==========================================
# 1. كل الحقول في الموديول ده مربوطة بـ users جوه نفس الملف (ForeignKey موجود فعلاً).
# 2. الموديولات التانية بتشاور على users.id (من عندي):
#    - subscriptions.student_id, payments.payer_user_id / reviewed_by,
#      requests.requester_id / decided_by  -> بعد الدمج نضيف ForeignKey("users.id")
# 3. relationship (اختياري): User.guardians / Guardian.student لو الـ services محتاجاها.
