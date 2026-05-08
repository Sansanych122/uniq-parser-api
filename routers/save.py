from fastapi import APIRouter, HTTPException
from models.schemas import SaveCourseRequest
from services.supabase_writer import save_course_to_db

router = APIRouter()

@router.post("/save")
async def save_parsed_course(request: SaveCourseRequest):
    try:
        # Викликаємо функцію запису в базу даних
        course_id = await save_course_to_db(
            course_title=request.course_name,
            creator_id=request.creator_id,
            questions=request.questions
        )
        
        return {
            "status": "success",
            "message": f"Курс '{request.course_name}' успішно збережено як приватний!",
            "saved_questions_count": len(request.questions),
            "course_id": course_id
        }
    except Exception as e:
        # Якщо щось піде не так з БД, FastAPI поверне зрозумілу помилку 500
        raise HTTPException(status_code=500, detail=f"Помилка при збереженні в БД: {str(e)}")