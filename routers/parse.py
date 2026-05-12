from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
from services.file_router import route_and_parse_file
from core.config import settings

router = APIRouter()

# Шлях змінено на /parse-file, як очікує фронтенд
@router.post("/parse-file")
async def parse_file_endpoint(
    file: UploadFile = File(...),
    options_count: Optional[int] = Form(None) # Додано для нової стратегії
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не вибрано")

    file_bytes = await file.read()
    
    # Валідація розміру
    if len(file_bytes) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Файл занадто великий (максимум {settings.MAX_FILE_SIZE_MB} MB)")

    # ПРИМІТКА: переконайтеся, що ваш file_router.py приймає options_count!
    # Наприклад: async def route_and_parse_file(filename, file_bytes, options_count=None):
    parsed_questions = await route_and_parse_file(file.filename, file_bytes, options_count)

    return {
        "status": "success",
        "filename": file.filename,
        "parsed_questions_count": len(parsed_questions),
        "questions": parsed_questions  
    }