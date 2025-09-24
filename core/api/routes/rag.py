from fastapi import APIRouter

from core.api.controllers.rag_controller import RagController
from core.api.schemas.rag_schemas import IngestRequest, QARequest, PrereqRequest

router = APIRouter()


@router.post("/rag/ncert/ingest")
async def ncert_ingest(req: IngestRequest):
    """Ingest NCERT PDFs for RAG system"""
    return await RagController.ncert_ingest(req)


@router.get("/rag/ncert/status")
async def ncert_ingest_status():
    """Get NCERT ingestion status"""
    return await RagController.ncert_ingest_status()


@router.post("/rag/ncert/qa")
async def ncert_qa(req: QARequest):
    """NCERT Q&A with vector similarity search"""
    return await RagController.ncert_qa(req)


@router.post("/rag/ncert/ingest-all")
async def ncert_ingest_all():
    """Ingest all NCERT content"""
    return await RagController.ncert_ingest_all()


@router.post("/rag/ncert/prerequisites")
async def ncert_prerequisites(req: PrereqRequest):
    """Discover prerequisites using vector search with floor-wise fallback"""
    return await RagController.ncert_prerequisites(req)