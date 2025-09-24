import os
import hashlib
import asyncio
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Optional PDF dependencies handled gracefully
try:
    from PyPDF2 import PdfReader  # type: ignore
except Exception:  # pragma: no cover
    PdfReader = None  # type: ignore
try:
    from pdfminer.high_level import extract_text as pdfminer_extract_text  # type: ignore
except Exception:  # pragma: no cover
    pdfminer_extract_text = None  # type: ignore

from services.ai.pinecone_client import (
    generate_embedding,
    upsert_vectors,
    is_pinecone_available,
)


NCERT_INDEX = "educational_content_ncert"


@dataclass
class IngestChunk:
    id: str
    text: str
    metadata: Dict[str, Any]


class NcertIngestStatus:
    def __init__(self) -> None:
        self.running: bool = False
        self.last_run: Optional[str] = None
        self.total_files: int = 0
        self.processed_files: int = 0
        self.total_chunks: int = 0
        self.upserted: int = 0
        self.errors: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "running": self.running,
            "last_run": self.last_run,
            "total_files": self.total_files,
            "processed_files": self.processed_files,
            "total_chunks": self.total_chunks,
            "upserted": self.upserted,
            "errors": self.errors[-10:],
        }


STATUS = NcertIngestStatus()


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8", errors="ignore")).hexdigest()


def _infer_metadata_from_path(file_path: str) -> Dict[str, Any]:
    # Example: CBSE/grade_10/ch (1).pdf
    parts = file_path.replace("\\", "/").split("/")
    grade = None
    chapter = None
    if len(parts) >= 2:
        # parts[-2] is grade directory
        grade_dir = parts[-2].lower()
        if "grade" in grade_dir:
            grade = grade_dir
    # crude chapter inference from filename
    fname = os.path.basename(file_path)
    chapter = os.path.splitext(fname)[0]
    meta = {
        "board": "CBSE",
        "grade_level": grade or "unknown",
        "chapter": chapter,
        "file_path": file_path,
    }
    # Derive a simple subject guess if present in a parent folder name
    # e.g., CBSE/grade_10/physics/ch (1).pdf
    lower = file_path.lower()
    for subj in ("physics", "chemistry", "mathematics", "biology", "english", "science", "history", "geography"):
        if f"/{subj}/" in lower or lower.endswith(f"/{subj}.pdf"):
            meta["subject"] = subj
            break
    return meta


def _extract_pdf_text_pages(file_path: str) -> List[Tuple[int, str]]:
    pages: List[Tuple[int, str]] = []
    py_ok = False
    # First attempt: PyPDF2
    if PdfReader is not None:
        try:
            reader = PdfReader(file_path)
            for i, page in enumerate(reader.pages):
                try:
                    txt = page.extract_text() or ""
                except Exception:
                    txt = ""
                if txt.strip():
                    pages.append((i + 1, txt))
            py_ok = True
        except Exception:
            py_ok = False

    # Fallback: pdfminer.six page-wise extraction if no text found
    if not pages and pdfminer_extract_text is not None:
        try:
            # Determine page count via PyPDF2 if available; else try sequential until stops (cap at 500 pages)
            max_pages = 0
            if PdfReader is not None:
                try:
                    max_pages = len(PdfReader(file_path).pages)
                except Exception:
                    max_pages = 0
            if max_pages <= 0:
                max_pages = 500
            for i in range(max_pages):
                try:
                    text_i = pdfminer_extract_text(file_path, page_numbers=[i]) or ""
                except Exception:
                    break
                if not text_i and i > 0:
                    # heuristic: stop on first empty after some progress
                    if len(pages) > 0:
                        break
                if text_i.strip():
                    pages.append((i + 1, text_i))
            if pages:
                return pages
        except Exception:
            pass

    # If still empty, surface a clear error guidance for OCR requirement
    if not pages:
        raise RuntimeError(
            "No extractable text found. PDF likely scanned. Install OCR pipeline (e.g., pdf2image + pytesseract) or provide text-based PDFs."
        )
    return pages


def _chunk_text(text: str, page: int, base_meta: Dict[str, Any], chunk_size: int = 2200, overlap: int = 300) -> List[IngestChunk]:
    chunks: List[IngestChunk] = []
    n = len(text)
    start = 0
    idx = 0
    while start < n:
        end = min(n, start + chunk_size)
        chunk_text = text[start:end]
        content_hash = _sha256(f"{base_meta.get('file_path')}|{page}|{idx}|{chunk_text[:64]}")
        meta = {
            **base_meta,
            "page_start": page,
            "page_end": page,
            "chunk_index": idx,
            "content_hash": content_hash,
            "content_type": "ncert_pdf",
        }
        chunk_id = _sha256(f"{meta['file_path']}|{page}|{idx}|{meta['content_hash']}")
        chunks.append(IngestChunk(id=chunk_id, text=chunk_text, metadata=meta))
        if end == n:
            break
        start = max(end - overlap, 0)
        idx += 1
    return chunks


async def _embed_and_upsert(chunks: List[IngestChunk]) -> int:
    # batch embed and upsert
    BATCH = 100
    upserted_total = 0
    for i in range(0, len(chunks), BATCH):
        batch = chunks[i : i + BATCH]
        vectors: List[Dict[str, Any]] = []
        # generate embeddings sequentially to keep memory bounded; could parallelize if needed
        for c in batch:
            vec = await generate_embedding(c.text)
            vectors.append({
                "id": c.id,
                "vector": vec,
                "metadata": c.metadata,
            })
        ok = await upsert_vectors(NCERT_INDEX, vectors)
        if ok:
            upserted_total += len(vectors)
    return upserted_total


async def ingest_ncert_pdfs(paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Ingest NCERT PDFs from CBSE/ folder into Pinecone.
    paths: optional list of file or directory paths to limit scope.
    """
    if not is_pinecone_available():
        raise RuntimeError("Pinecone not available. Set PINECONE_API_KEY and initialize indexes.")

    STATUS.running = True
    STATUS.errors.clear()
    STATUS.total_files = 0
    STATUS.processed_files = 0
    STATUS.total_chunks = 0
    STATUS.upserted = 0

    # resolve targets
    targets: List[str] = []
    if paths:
        for p in paths:
            if os.path.isdir(p):
                for root, _, files in os.walk(p):
                    for f in files:
                        if f.lower().endswith(".pdf"):
                            targets.append(os.path.join(root, f))
            elif os.path.isfile(p) and p.lower().endswith(".pdf"):
                targets.append(p)
    else:
        base = os.path.join("CBSE")
        if os.path.isdir(base):
            for root, _, files in os.walk(base):
                for f in files:
                    if f.lower().endswith(".pdf"):
                        targets.append(os.path.join(root, f))

    STATUS.total_files = len(targets)

    try:
        for file_path in targets:
            try:
                meta = _infer_metadata_from_path(file_path)
                pages = _extract_pdf_text_pages(file_path)
                file_chunks: List[IngestChunk] = []
                for page_num, page_text in pages:
                    # light cleanup
                    text = "\n".join([line.strip() for line in page_text.splitlines()])
                    file_chunks.extend(_chunk_text(text, page_num, meta))
                if not file_chunks:
                    STATUS.errors.append(f"{file_path}: no extractable text (empty after parsing)")
                STATUS.total_chunks += len(file_chunks)
                if file_chunks:
                    added = await _embed_and_upsert(file_chunks)
                    if added:
                        STATUS.upserted += added
                    else:
                        STATUS.errors.append(f"{file_path}: upsert returned False (no vectors added)")
            except Exception as e:  # continue on error, record
                STATUS.errors.append(f"{file_path}: {e}")
            finally:
                STATUS.processed_files += 1
        STATUS.running = False
        STATUS.last_run = datetime.utcnow().isoformat()
    finally:
        STATUS.running = False

    return STATUS.to_dict()


async def get_ingest_status() -> Dict[str, Any]:
    return STATUS.to_dict()


