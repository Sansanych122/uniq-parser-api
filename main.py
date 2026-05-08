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
    allow_origins=["http://localhost:5173", "https://uniquiz.pages.dev"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Підключаємо наші роути
app.include_router(parse.router)
app.include_router(save.router)

@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Сервер працює і готовий до роботи!"}