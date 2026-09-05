import re
import fitz  


def extract_text_from_pdf(file_path: str) -> str:
    
    doc = fitz.open(file_path)

    full_text = ""
    for page in doc:
        full_text += page.get_text()

    doc.close()

    return full_text


def extract_text_and_links_from_pdf(file_path: str) -> tuple[str, list[str]]:

    doc = fitz.open(file_path)

    full_text = ""
    links = []
    for page in doc:
        full_text += page.get_text()
        for link in page.get_links():
            uri = link.get("uri")
            if uri:
                links.append(uri)

    doc.close()

    return full_text, links


def redact_pii(text: str) -> str:
    
    text = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '[EMAIL REDACTED]', text)
    text = re.sub(r'(\+?\d[\d\s\-\(\)]{7,}\d)', '[PHONE REDACTED]', text)
    return text


LINKEDIN_PATTERN = re.compile(r'(https?://)?(www\.)?linkedin\.com/in/[A-Za-z0-9\-_/]+', re.IGNORECASE)
GITHUB_PATTERN = re.compile(r'(https?://)?(www\.)?github\.com/[A-Za-z0-9\-_/]+', re.IGNORECASE)


def _find_url(pattern: re.Pattern, pdf_links: list[str], cv_text: str) -> str | None:
    for url in pdf_links:
        if pattern.search(url):
            return url
    match = pattern.search(cv_text)
    return match.group(0) if match else None


def extract_contact_info(cv_text: str, pdf_links: list[str] | None = None) -> dict:

    pdf_links = pdf_links or []

    email = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', cv_text)
    phone = re.search(r'(\+?\d[\d\s\-\(\)]{7,}\d)', cv_text)

    return {
        "email": email.group(0) if email else None,
        "phone": phone.group(0) if phone else None,
        "linkedin_url": _find_url(LINKEDIN_PATTERN, pdf_links, cv_text),
        "github_url": _find_url(GITHUB_PATTERN, pdf_links, cv_text),
    }

MAX_CV_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
def validate_pdf_upload(contents: bytes) -> str | None:
    if len(contents) == 0:
        return "Empty file."
    if len(contents) > MAX_CV_SIZE_BYTES:
        return "File too large. Maximum size is 5 MB."
    if not contents.startswith(b"%PDF"):
        return "Invalid file type. Only PDF files are accepted."
    return None