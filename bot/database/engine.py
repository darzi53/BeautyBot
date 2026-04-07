from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def create_tables() -> None:
    from bot.database.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
