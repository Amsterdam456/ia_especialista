from pathlib import Path
from typing import List

import docx
import pdfplumber


def extract_text_from_file(path: str | Path) -> List[str]:
    """
    Detecta o tipo de arquivo e retorna SEMPRE uma lista de páginas:
    ["texto da página 1", "texto da página 2", ...]
    """
    path = Path(path)
    ext = path.suffix.lower()

    if ext == ".pdf":
        return extract_pdf_pages(path)

    if ext == ".docx":
        return extract_docx_pages(path)

    if ext == ".txt":
        return extract_txt_pages(path)

    return []


# ----------------------------------------------------------------------
# PDF → Lista de páginas
# ----------------------------------------------------------------------
def extract_pdf_pages(path: Path) -> List[str]:
    pages: List[str] = []
    try:
        with pdfplumber.open(str(path)) as pdf:
            for page in pdf.pages:
                # Melhor extração possível
                content = page.extract_text(layout=True)
                if not content:
                    content = page.extract_text()

                pages.append(clean_text(content or ""))
    except Exception:
        return []

    return pages


# ----------------------------------------------------------------------
# DOCX → Trata cada parágrafo como "bloco"
# (não existe página real, mas simulamos páginas virtuais)
# ----------------------------------------------------------------------
def extract_docx_pages(path: Path) -> List[str]:
    try:
        doc = docx.Document(str(path))
        paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
        text = "\n".join(paragraphs)
        return split_long_text_into_pages(text)
    except Exception:
        return []


# ----------------------------------------------------------------------
# TXT → converte em "páginas virtuais" para manter padrão
# ----------------------------------------------------------------------
def extract_txt_pages(path: Path) -> List[str]:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        return split_long_text_into_pages(text)
    except Exception:
        return []


# ----------------------------------------------------------------------
# Funções auxiliares
# ----------------------------------------------------------------------
def clean_text(text: str) -> str:
    """Remove espaços e linhas inúteis."""
    if not text:
        return ""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return "\n".join(lines)


def split_long_text_into_pages(text: str, max_chars: int = 2500) -> List[str]:
    """
    Divide textos longos (docx/txt) em blocos tipo 'página virtual'
    para manter consistência com os PDFs.
    """
    cleaned = clean_text(text)
    if not cleaned:
        return []

    pages = []
    start = 0
    length = len(cleaned)

    while start < length:
        end = start + max_chars
        pages.append(cleaned[start:end])
        start = end

    return pages
