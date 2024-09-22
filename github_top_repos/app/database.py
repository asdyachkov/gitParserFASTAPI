import asyncpg
from .config import settings


async def get_db_connection():
    return await asyncpg.connect(settings.database_url)
