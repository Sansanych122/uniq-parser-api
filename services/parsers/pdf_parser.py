import io
import fitz  # PyMuPDF
from services.parsers.txt_parser import parse_txt_content

def parse_pdf_content(file_bytes: bytes) -> list:
    """
    Етап 0: Видобування тексту з PDF.
    Використовує режим 'sort=True' для збереження логічної послідовності читання.
    """
    pdf_file = io.BytesIO(file_bytes)
    
    try:
        # Відкриваємо документ з байтового потоку
        doc = fitz.open(stream=pdf_file, filetype="pdf")
        
        full_text = ""
        for page in doc:
            # Витягуємо текст, сортуючи блоки згори вниз та зліва направо
            # Це допомагає уникнути "каші", якщо в PDF є колонки
            full_text += page.get_text("text", sort=True) + "\n"
            
        doc.close()
        
        # Передаємо видобутий текст у Pipeline (Strategy Strict -> Strategy Flexible)
        return parse_txt_content(full_text)
        
    except Exception as e:
        raise Exception(f"Критична помилка двигуна PyMuPDF: {str(e)}")