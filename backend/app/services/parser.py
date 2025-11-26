import pdfplumber
import docx

def extract_text_from_file(path):
    if path.lower().endswith(".pdf"):
        return extract_pdf(path)
    if path.lower().endswith(".docx"):
        return extract_docx(path)
    return ""

def extract_pdf(path):
    text = ""
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def extract_docx(path):
    doc = docx.Document(path)
    return "\n".join([p.text for p in doc.paragraphs])
