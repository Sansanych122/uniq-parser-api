from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from services.file_router import route_and_parse_file
from core.config import settings

router = APIRouter()

@router.post("/parse")
async def parse_file_endpoint(
    course_name: str = Form(...), 
    file: UploadFile = File(...)
):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Файл не вибрано")

    file_bytes = await file.read()
    
    # Валідація розміру
    if len(file_bytes) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Файл занадто великий (максимум {settings.MAX_FILE_SIZE_MB} MB)")

    # Передаємо у File Router (Крок ① -> ② -> ③ з твого плану)
    parsed_questions = await route_and_parse_file(file.filename, file_bytes)

    # Повертаємо результат на фронтенд
    return {
        "status": "success",
        "course_name": course_name,
        "filename": file.filename,
        "parsed_questions_count": len(parsed_questions),
        "questions": parsed_questions  # ВІДДАЄМО ВСІ ПИТАННЯ!
    }