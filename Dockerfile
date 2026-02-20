FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей для сборки некоторых библиотек
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Команда по умолчанию теперь запускает массовое исследование
CMD ["python", "src/mass_research.py"]