import asyncpg
from asyncpg.pool import Pool
from fastapi import FastAPI, Request, Depends
from contextlib import asynccontextmanager
from .config import settings


# Создание пула соединений
async def init_db_pool(app: FastAPI):
    app.state.db_pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=5,  # Минимум 5 соединений
        max_size=20,  # Максимум 20 соединений
        max_inactive_connection_lifetime=300,  # 5 минут неактивные соединения могут быть открыты
        timeout=10.0  # 10 секунд ожидания для получения соединения из пула
    )


# Закрытие пула соединений
async def close_db_pool(app: FastAPI):
    await app.state.db_pool.close()


# Получение пула соединений из состояния приложения
def get_db_pool(request: Request) -> Pool:
    return request.app.state.db_pool


# Контекстный менеджер для соединения с БД
@asynccontextmanager
async def get_db_connection(db_pool: Pool = Depends(get_db_pool)):
    conn = await db_pool.acquire()
    try:
        yield conn  # Возвращаем соединение
    finally:
        await db_pool.release(conn)  # Освобождаем соединение обратно в пул
