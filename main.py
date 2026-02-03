from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routers import auth, notes
from src.database import create_tables
import logging

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Создаем таблицы при запуске
try:
    create_tables()
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {e}")

app = FastAPI(
    title="Notes API",
    description="API для управления заметками с аутентификацией",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене нужно указать конкретные домены
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(notes.router, prefix="/notes", tags=["Notes"])

@app.get("/health", tags=["Health"])
async def health_check():
    """Проверка работоспособности сервера"""
    return {"status": "healthy", "message": "Server is running"}

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up Notes API server")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Notes API server")

if __name__ == "__main__":
    import uvicorn
    # В продакшене лучше использовать gunicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
