FROM python:3.11-alpine

# Устанавливаем зависимости
WORKDIR /app

# Копируем requirements.txt
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY . .

# Создаем директории для данных и логов
RUN mkdir -p /app/data /app/logs

# Устанавливаем права
RUN chown -R nobody:nobody /app

# Меняем пользователя на nobody для безопасности
USER nobody

# Экспорт порта
EXPOSE 8000

# Запуск приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
