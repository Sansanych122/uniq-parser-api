import io
from docx import Document
from services.parsers.txt_parser import parse_txt_content

def parse_docx_content(file_bytes: bytes) -> list:
    """
    Етап 0: Видобування тексту з DOCX.
    Збирає текст з абзаців та таблиць для максимального охоплення даних.
    """
    docx_file = io.BytesIO(file_bytes)
    
    try:
        doc = Document(docx_file)
        text_blocks = []

        # 1. Збираємо текст з усіх абзаців
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_blocks.append(paragraph.text)

        # 2. Додатково збираємо текст з таблиць (про всяк випадок)
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_text:
                    text_blocks.append(" ".join(row_text))

        # Об'єднуємо все в один масив тексту з роздільниками
        full_text = "\n".join(text_blocks)
        
        # Відправляємо на конвеєр Pipeline
        return parse_txt_content(full_text)
        
    except Exception as e:
        raise Exception(f"Помилка структури DOCX документа: {str(e)}")