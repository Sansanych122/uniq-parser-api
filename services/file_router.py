import os
from fastapi import HTTPException
from services.parsers.pdf_parser import parse_pdf_content
from services.parsers.docx_parser import parse_docx_content
from services.parsers.txt_parser import parse_txt_content

async def route_and_parse_file(filename: str, file_bytes: bytes, options_count: int = None) -> list:
    """
    Маршрутизатор файлів. Визначає формат файлу за розширенням 
    і передає байти у відповідний спеціалізований парсер разом із підказкою options_count.
    """
    ext = os.path.splitext(filename)[1].lower()

    try:
        if ext == '.pdf':
            # Передаємо байти та кількість варіантів
            return parse_pdf_content(file_bytes, options_count)
            
        elif ext in ['.docx', '.doc']:
            # Передаємо байти, ім'я файлу (для перевірки старих .doc) та кількість варіантів
            return parse_docx_content(file_bytes, filename, options_count)
            
        elif ext == '.txt':
            # Для TXT спочатку декодуємо байти в рядок, враховуючи можливе кириличне кодування
            try:
                text_content = file_bytes.decode('utf-8')
            except UnicodeDecodeError:
                text_content = file_bytes.decode('cp1251')
                
            # Передаємо текст та кількість варіантів
            return parse_txt_content(text_content, options_count)
            
        else:
            raise HTTPException(status_code=400, detail=f"Формат файлу {ext} не підтримується системою.")
            
    except Exception as e:
        # Прокидаємо помилку вище, щоб FastAPI міг повернути її на фронтенд
        raise e