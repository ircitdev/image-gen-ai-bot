# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта
COPY . .

# Создаем директории для данных если они не существуют
RUN mkdir -p /app/data

# Переменные окружения (будут переопределены через .env или docker-compose)
ENV PYTHONUNBUFFERED=1

# Запускаем бота
CMD ["python", "bot.py"]
