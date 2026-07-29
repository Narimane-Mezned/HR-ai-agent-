
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



def extract_contact_info(cv_text: str) -> dict:
    
    email = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', cv_text)
    phone = re.search(r'(\+?\d[\d\s\-\(\)]{7,}\d)', cv_text)
    linkedin = re.search(r'(https?://)?(www\.)?linkedin\.com/in/[A-Za-z0-9\-_/]+', cv_text, re.IGNORECASE)
    github = re.search(r'(https?://)?(www\.)?github\.com/[A-Za-z0-9\-_/]+', cv_text, re.IGNORECASE)

    return {
        "email": email.group(0) if email else None,
        "phone": phone.group(0) if phone else None,
        "linkedin_url": linkedin.group(0) if linkedin else None,
        "github_url": github.group(0) if github else None,
    }