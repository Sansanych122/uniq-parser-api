from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import parse, save

app = FastAPI(
    title="UniQ Parser API",
    description="Мікросервіс для парсингу навчальних тестів",
    version="1.0.0"
)

# Налаштування CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Підключаємо наші роути з префіксом /api
app.include_router(parse.router, prefix="/api")
app.include_router(save.router, prefix="/api")

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Сервер працює і готовий до роботи!"}