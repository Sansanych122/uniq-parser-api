import io
from typing import Optional
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from routers import parse, save
from services.gemini_service import generate_tests_via_gemini

# Ініціалізація додатка (тепер люстра висить там, де треба)
app = FastAPI(
    title="UniQ Parser API",
    description="Мікросервіс для парсингу навчальних тестів",
    version="1.0.0"
)

# Налаштування CORS (щоб фронтенд не бився в конвульсіях від блокувань)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Підключаємо твої старі класичні роути
app.include_router(parse.router, prefix="/api")
app.include_router(save.router, prefix="/api")

# Новий ендпоінт для божественної ШІ-генерації
@app.post("/api/generate-ai-tests")
async def generate_ai_tests_endpoint(
    file: UploadFile = File(...),
    questions_count: int = Form(5),
    ai_prompt: Optional[str] = Form("")
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл загубився по дорозі. Спробуй ще раз.")

    content_bytes = await file.read()
    filename = file.filename.lower()
    extracted_text = ""

    try:
        # Конвертуємо файли в голий текст, щоб не платити Google за те, що ми вміємо самі
        if filename.endswith('.pdf'):
            import fitz
            doc = fitz.open(stream=content_bytes, filetype="pdf")
            extracted_text = "\n".join([page.get_text() for page in doc])
            doc.close()
            
        elif filename.endswith('.docx') or filename.endswith('.doc'):
            from docx import Document
            doc = Document(io.BytesIO(content_bytes))
            extracted_text = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            
        elif filename.endswith('.txt'):
            try:
                extracted_text = content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                extracted_text = content_bytes.decode('cp1251')
        else:
            raise HTTPException(status_code=400, detail="Формат не підтримується. Тільки PDF, DOCX або TXT.")

        if len(extracted_text.strip()) < 50:
            raise HTTPException(status_code=400, detail="Тексту замало. З трьох слів я тести не згенерую.")

        # Передаємо текст на з'їдіння Gemini API
        ai_questions = generate_tests_via_gemini(
            context_text=extracted_text, 
            questions_count=questions_count, 
            user_refinement=ai_prompt
        )

        return {
            "status": "success",
            "parsed_questions_count": len(ai_questions),
            "questions": ai_questions
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Стандартний чек працездатності сервера
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "Сервер працює і готовий до роботи!"}