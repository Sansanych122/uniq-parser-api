import math
from supabase import create_client, Client
from core.config import settings
from models.schemas import QuestionSchema

# Ініціалізуємо клієнт Supabase
supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

async def save_course_to_db(course_title: str, creator_id: str, questions: list[QuestionSchema]) -> str:
    total_q = len(questions)
    
    # 1. Створюємо ПРИВАТНИЙ Курс
    new_course = supabase.table("courses").insert({
        "title": course_title,
        "description": "Приватний курс, доданий користувачем",
        "is_public": False,           # <-- ТІЛЬКИ ДЛЯ АВТОРА
        "creator_id": creator_id      # <-- ПРИВ'ЯЗКА ДО ПРОФІЛЮ
    }).execute()
    
    course_id = new_course.data[0]['id']

    # 2. Розрахунок частин (орієнтир ~250 питань на частину)
    if total_q <= 300:
        k = 1
    else:
        k = math.ceil(total_q / 250.0)
        
    base_size = total_q // k
    remainder = total_q % k

    # 3. Розбиваємо на розділи і завантажуємо
    start_idx = 0
    for i in range(k):
        current_size = base_size + (1 if i < remainder else 0)
        chunk = questions[start_idx : start_idx + current_size]
        
        section_title = f"{course_title} - Part {i + 1}"
        
        # Створюємо Розділ (Section)
        new_section = supabase.table("sections").insert({
            "course_id": course_id,
            "title": section_title,
            "order_index": i + 1
        }).execute()
        section_id = new_section.data[0]['id']

        # Підготовлюємо питання для пакетного запису (batch insert)
        db_questions = []
        for q in chunk:
            db_questions.append({
                "section_id": section_id,
                "content": q.content,
                "options": q.options, 
                "correct_answer": q.correct_answer
            })

        # Записуємо всі питання цієї частини одним запитом
        if db_questions:
            supabase.table("questions").insert(db_questions).execute()
        
        start_idx += current_size

    return course_id