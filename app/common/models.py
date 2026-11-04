import uuid
from datetime import datetime
from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
  """الفئة الأساسية التي ترث منها جميع نماذج المشروع"""

  pass


class BaseModel(Base):
  """فئة مجردة تورث المعرف الموحد والتوقيتات لجميع الجداول.

  لن يتم إنشاء جدول مستقل في قاعدة البيانات لهذه الفئة.
  """

  __abstract__ = True

  id: Mapped[uuid.UUID] = mapped_column(
      UUID(as_uuid=True),
      primary_key=True,
      default=uuid.uuid4,
      server_default=func.gen_random_uuid(),
      index=True,
      comment="المعرف الفريد للسجل",
  )
  created_at: Mapped[datetime] = mapped_column(
      DateTime(timezone=True),
      server_default=func.now(),
      nullable=False,
      comment="توقيت الإنشاء الموحد",
  )
  updated_at: Mapped[datetime] = mapped_column(
      DateTime(timezone=True),
      server_default=func.now(),
      onupdate=func.now(),
      nullable=False,
      comment="توقيت آخر تحديث",
  )