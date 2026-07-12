
import re
import fitz  


def extract_text_from_pdf(file_path: str) -> str:
    
    doc = fitz.open(file_path)

    full_text = ""
    for page in doc:
        full_text += page.get_text()

    doc.close()

    return full_text


def redact_pii(text: str) -> str:
    
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL REDACTED]', text)
    text = re.sub(r'(\+?\d[\d\s\-\(\)]{7,}\d)', '[PHONE REDACTED]', text)
    return text