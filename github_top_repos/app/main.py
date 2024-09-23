from fastapi import FastAPI
from .routers import repos
from .database import init_db_pool, close_db_pool

app = FastAPI()


# Событие при запуске приложения
@app.on_event("startup")
async def on_startup():
    await init_db_pool(app)  # Инициализируем пул соединений


# Событие при завершении работы приложения
@app.on_event("shutdown")
async def on_shutdown():
    await close_db_pool(app)  # Закрываем пул соединений


# Подключаем маршруты
app.include_router(repos.router, prefix="/api/repos")
