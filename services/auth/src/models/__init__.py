"""
Auth Service Models
"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from src.config import settings

# Базовый класс для всех моделей
Base = declarative_base()

# Создаем асинхронный движок
engine = create_async_engine(settings.database_url, echo=True)

# Создаем фабрику сессий (используем async_sessionmaker)
async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db():
    """Dependency for getting DB session"""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database (create tables)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# Импортируем модели здесь, чтобы они были зарегистрированы в Base
# Важно: импорт моделей должен быть после определения Base и перед init_db
from src.models.user import User
from src.models.token import VerificationToken
