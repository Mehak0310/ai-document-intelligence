import io
from pathlib import Path

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from .errors import AppError


def validate_pdf(filename, contents, limit):
    name = Path(str(filename or "").replace("\\", "/")).name
    if not name.lower().endswith(".pdf"):
        raise AppError("Only PDF files are supported.", 415)
    if len(name) > 200 or any(ord(c) < 32 for c in name):
        raise AppError("Invalid PDF filename.")
    if len(contents) > limit:
        raise AppError("PDF exceeds the configured upload limit.", 413)
    if not contents.lstrip().startswith(b"%PDF-"):
        raise AppError("The uploaded file is not a valid PDF.")
    return name


def parse_chunks(contents, document_id, settings):
    try:
        reader = PdfReader(io.BytesIO(contents))
        if reader.is_encrypted:
            raise AppError("Encrypted PDFs are not supported.")
        pages = [Document(page_content=page.extract_text() or "", metadata={"page": i + 1}) for i, page in enumerate(reader.pages)]
        documents = RecursiveCharacterTextSplitter(chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap).split_documents(pages)
    except AppError:
        raise
    except Exception as exc:
        raise AppError("PDF could not be parsed. Use a text-based, unencrypted PDF.") from exc
    chunks = [{"id": f"{document_id}:{i}", "page": d.metadata["page"], "text": d.page_content} for i, d in enumerate(documents) if d.page_content.strip()]
    if not chunks:
        raise AppError("No readable text was found. Scanned PDFs require OCR, which is not supported.")
    if len(chunks) > settings.max_chunks:
        raise AppError("Document exceeds the configured chunk limit.", 413)
    return chunks
