from fastapi import HTTPException
from services.parsers.txt_parser import parse_txt_content
from services.parsers.pdf_parser import parse_pdf_content
from services.parsers.docx_parser import parse_docx_content

async def route_and_parse_file(filename: str, file_bytes: bytes) -> list:
    """Визначає тип файлу і направляє його у відповідний парсер"""
    
    extension = filename.split('.')[-1].lower()
    
    if extension == 'txt':
        try:
            text_content = file_bytes.decode('utf-8')
            return parse_txt_content(text_content)
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Помилка кодування. Збережіть TXT файл у форматі UTF-8")
            
    elif extension == 'pdf':
        try:
            return parse_pdf_content(file_bytes)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Помилка читання PDF файлу: {str(e)}")
            
    elif extension == 'docx':
        try:
            return parse_docx_content(file_bytes)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Помилка читання DOCX файлу: {str(e)}")
            
    else:
        raise HTTPException(status_code=400, detail="Непідтримуваний формат файлу. Завантажте .txt, .pdf або .docx")