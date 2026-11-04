"""

SUtech Smart Transport System - Core Application Configuration

الوصف:
    ملف إدارة الإعدادات المركزية للمشروع باستخدام Pydantic Settings.

الوظيفة والآلية الهندسية:
    1. القراءة الديناميكية: يبحث عن ملف البيئة المحلي (.env) لقراءة المتغيرات الحساسة تلقائياً.
    2. شبكة أمان موحدة (Fallback): في حال عدم وجود ملف .env محلياً على جهاز أحد أعضاء الفريق،
       يوفر الكلاس رابط اتصال افتراضي بحاوية PostgreSQL و Docker المتفق عليها محلياً.
    3. التكامل مع Alembic: يوفر كائن الإعدادات (settings) كمرجع موحد في بايثون
       بدلاً من كتابة الروابط الثابتة في alembic.ini، مما يمنع التضارب عند الرفع والتشغيل.

"""
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # رابط الاتصال بقاعدة البيانات الافتراضية عبر المحرك غير المتزامن (asyncpg)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/sutech_transport"

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"  # تجاهل أي متغيرات إضافية في .env دون إيقاف التطبيق
    )

# كائن الإعدادات العام الجاهز للاستيراد في كافة أرجاء المشروع
settings = Settings()