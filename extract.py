import fitz
import os
import re


def extract_text_from_pdf(pdf_path: str) -> dict:
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    warnings = []
    pages = []

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        raise ValueError(f"Could not open PDF: {e}")

    total_pages_raw = len(doc)

    for page_num in range(total_pages_raw):
        page = doc[page_num]
        raw_text = page.get_text()
        cleaned = _clean_text(raw_text)
        word_count = len(cleaned.split()) if cleaned else 0
        is_empty = word_count == 0

        if is_empty:
            warnings.append(
                f"Page {page_num + 1} has no extractable text "
                f"(may be a scanned image or a blank page)."
            )

        pages.append({
            "page_number": page_num + 1,
            "text": cleaned,
            "word_count": word_count,
            "is_empty": is_empty
        })

    doc.close()

    content_pages = [p for p in pages if not p["is_empty"]]

    if not content_pages:
        raise ValueError(
            "No text could be extracted from this PDF. "
            "It may be a scanned document. OCR support is not yet available."
        )

    full_text = "\n\n".join(p["text"] for p in content_pages)
    total_words = sum(p["word_count"] for p in content_pages)
    language_hint = _detect_language(full_text)


    if total_words < 100:
        warnings.append(
            f"Document is very short ({total_words} words). "
            "Quiz generation may produce limited results.")

    return {
        "full_text": full_text,
        "pages": pages,
        "total_pages": len(content_pages),
        "total_pages_raw": total_pages_raw,
        "total_words": total_words,
        "language_hint": language_hint,
        "warnings": warnings
    }





def _clean_text(raw: str) -> str:
    if not raw:
        return ""

    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', raw)

    text = re.sub(r'-\n(\w)', r'\1', text)

    text = re.sub(r'\n{3,}', '\n\n', text)

    text = re.sub(r'[ \t]{2,}', ' ', text)

    return text.strip()


def _detect_language(text: str) -> str:
    arabic_chars = len(re.findall(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]', text))
    latin_chars = len(re.findall(r'[a-zA-Z]', text))
    total = arabic_chars + latin_chars

    if total == 0:
        return "unknown"

    arabic_ratio = arabic_chars / total

    if arabic_ratio > 0.75:
        return "arabic"
    elif arabic_ratio < 0.25:
        return "english"
    else:
        return "mixed"


def _make_section(existing: list, buffer_pages: list, buffer_words: int) -> dict:
    return {
        "section_number": len(existing) + 1,
        "text": "\n\n".join(p["text"] for p in buffer_pages),
        "pages": [p["page_number"] for p in buffer_pages],
        "word_count": buffer_words
    }


def _estimate_sections(pdf_data: dict) -> int:
    return max(1, pdf_data["total_words"] // 150)


def _estimate_chunks(pdf_data: dict) -> int:
    effective_words = pdf_data["total_words"]
    chunk_size = 600
    overlap = 75
    if effective_words <= chunk_size:
        return 1
    return max(1, (effective_words - overlap) // (chunk_size - overlap))