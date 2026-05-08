from pydantic import BaseModel, Field
from typing import List

class QuestionSchema(BaseModel):
    content: str = Field(..., description="Текст самого питання")
    options: List[str] = Field(..., description="Масив варіантів відповідей")
    correct_answer: str = Field(..., description="Правильна відповідь")

class SaveCourseRequest(BaseModel):
    course_name: str = Field(..., min_length=3, description="Назва нового курсу")
    creator_id: str = Field(..., description="ID користувача (профілю), який створює курс") # ВІДКРИЛИ ПОЛЕ
    questions: List[QuestionSchema] = Field(..., min_length=1, description="Масив питань")