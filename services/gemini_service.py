import os
import time
from google import genai
from google.genai import types
from google.genai.errors import APIError
from pydantic import BaseModel, Field
from fastapi import HTTPException

# Жорстка схема. Без фокусів.
class AIQuestionSchema(BaseModel):
    content: str = Field(description="Текст питання, без нумерації на початку")
    options: list[str] = Field(description="Масив варіантів відповідей (від 2 до 6 штук)")
    correct_answer: str = Field(description="Правильний варіант відповіді (обов'язково має бути точним текстом з масиву options)")

class AIQuizResponse(BaseModel):
    questions: list[AIQuestionSchema]

# Основна та резервна моделі
MODELS_FALLBACK_CHAIN = [
    "gemini-3.6-flash",       # Основна модель
    "gemini-3.5-flash-lite",  # Запасна легка модель
]

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

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_schema=AIQuizResponse,
        temperature=0.2, # Тримаємо температуру низькою, щоб не фантазував
    )

    last_error = None

    for model_name in MODELS_FALLBACK_CHAIN:
        # 2 спроби на кожну модель перед перемиканням
        for attempt in range(2):
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=full_prompt,
                    config=config,
                )
                
                # Перевіряємо та валідуємо відповідь
                validated_data = AIQuizResponse.model_validate_json(response.text)
                return [q.model_dump() for q in validated_data.questions]
                
            except APIError as e:
                last_error = e
                # Якщо сервер перевантажений (503) або вперлися в ліміти (429) — чекаємо і пробуємо ще / міняємо модель
                if e.code in [503, 429]:
                    print(f"⚠️ [{model_name}] Тимчасово недоступна (код {e.code}), спроба {attempt + 1}/2...")
                    time.sleep(1.5)
                    continue
                # При інших помилках API (наприклад, невалідний ключ) не ретраїмо
                break
            except Exception as e:
                last_error = e
                break

    print(f"🔥 АХТУНГ! Помилка генерації на всіх моделях: {str(last_error)}")
    raise HTTPException(status_code=500, detail=f"Google API впало в кому: {str(last_error)}")