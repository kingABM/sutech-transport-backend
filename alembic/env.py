import asyncio
from logging.config import fileConfig
import importlib
from pathlib import Path

from sqlalchemy import pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# 1. إعداد اللوجز
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 2. قراءة الرابط ديناميكياً من كود بايثون (من ملف config.py الذي يقرأ من .env)
from app.core.config import settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# 3. استيراد كلاس Base المشترك
from app.common.models import Base

# 4. تحميل ملفات models.py الموجودة مباشرة داخل مجلدات app/modules.
#    المجلدات تعمل كـ namespace packages، لذلك لا نعتمد على __init__.py.
modules_dir = Path(__file__).resolve().parents[1] / "app" / "modules"
for module_dir in modules_dir.iterdir():
    if module_dir.is_dir() and (module_dir / "models.py").is_file():
        importlib.import_module(f"app.modules.{module_dir.name}.models")

target_metadata = Base.metadata

def do_run_migrations(connection: Connection) -> None:
    # تفعيل إضافات بوستجرس المتقدمة تلقائياً
    connection.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
    connection.execute(text('CREATE EXTENSION IF NOT EXISTS "postgis";'))
    connection.execute(text('CREATE EXTENSION IF NOT EXISTS "vector";'))

    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        include_name=lambda name, type_, parent_names: not (
            type_ == "table" and name in ["spatial_ref_sys"]
        )
    )
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()
else:
    run_migrations_online()
