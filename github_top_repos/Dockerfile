FROM python:3.11-slim

# Копируем зависимости
COPY requirements.txt /requirements.txt

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r /requirements.txt

# Копируем всё приложение
COPY . /app

# Переходим в папку с приложением
WORKDIR /app

# Запуск FastAPI приложения
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
