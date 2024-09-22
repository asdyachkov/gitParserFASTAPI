from fastapi import FastAPI
from .routers import repos

app = FastAPI()

# Подключаем маршруты
app.include_router(repos.router, prefix="/api/repos")