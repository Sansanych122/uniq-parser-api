import io
import fitz  # PyMuPDF
from services.parsers.txt_parser import parse_txt_content

def parse_pdf_content(file_bytes: bytes, options_count: int = None) -> list:
    """
    Видобування тексту з PDF.
    Використовує sort=True для збереження читабельності колонок.
    """
    pdf_file = io.BytesIO(file_bytes)
    
    try:
        doc = fitz.open(stream=pdf_file, filetype="pdf")
        
        full_text = ""
        for page in doc:
            full_text += page.get_text("text", sort=True) + "\n"
            
        doc.close()
        
        # Передаємо видобутий текст ТА ПІДКАЗКУ у розумний Pipeline
        return parse_txt_content(full_text, options_count)
        
    except Exception as e:
        raise Exception(f"Помилка видобування тексту з PDF: {str(e)}")