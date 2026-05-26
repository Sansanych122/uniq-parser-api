import os
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from fastapi import HTTPException

# Жорстка схема. Без фокусів.
class AIQuestionSchema(BaseModel):
    content: str = Field(description="Текст питання, без нумерації на початку")
    options: list[str] = Field(description="Масив варіантів відповідей (від 2 до 6 штук)")
    correct_answer: str = Field(description="Правильний варіант відповіді (обов'язково має бути точним текстом з масиву options)")

class AIQuizResponse(BaseModel):
    questions: list[AIQuestionSchema]

def generate_tests_via_gemini(context_text: str, questions_count: int, user_refinement: str = "") -> list:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Ключ загубив? В .env немає GEMINI_API_KEY.")

    # Ініціалізація клієнта
    client = genai.Client(api_key=api_key)

    # УНІВЕРСАЛЬНИЙ ПРОМПТ
    system_instruction = (
        "Ти — професійний та надзвичайно точний генератор навчальних тестів. "
        "Твоя експертиза охоплює БУДЬ-ЯКІ теми: від ІТ та вищої математики до медицини, історії чи поп-культури. "
        "Твоє єдине завдання — витягнути тести з наданого тексту або згенерувати нові суворо на його основі. "
        f"Ти ПОВИНЕН згенерувати рівно {questions_count} питань. Не більше, не менше. "
        "Мова: виключно українська. Якщо є додаткові побажання користувача — виконай їх безумовно."
    )

    full_prompt = f"Контекст тексту (матеріал лекції/конспекту):\n{context_text}\n\n"
    if user_refinement:
        full_prompt += f"ДОДАТКОВІ НАКАЗИ ВІД КОРИСТУВАЧА: {user_refinement}\n\n"

    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=full_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=AIQuizResponse,
                temperature=0.2, # Тримаємо температуру низькою, щоб не фантазував
            ),
        )
        
        # Перевіряємо, чи ця залізяка дійсно повернула те, що ми просили
        validated_data = AIQuizResponse.model_validate_json(response.text)
        return [q.model_dump() for q in validated_data.questions]
        
    except Exception as e:
        print(f"🔥 АХТУНГ! Помилка генерації: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Google API впало в кому: {str(e)}")