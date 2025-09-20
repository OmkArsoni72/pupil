from fastapi import HTTPException
from typing import List, Dict, Any

from services.ai.ncert_ingest import ingest_ncert_pdfs, get_ingest_status
from services.ai.pinecone_client import generate_embedding, query_vectors, is_pinecone_available
from services.ai.floor_wise_prerequisite_discovery import discover_floor_wise_prerequisites

from api.schemas.rag_schemas import IngestRequest, QARequest, PrereqRequest


class RagController:

    @staticmethod
    async def ncert_ingest(req: IngestRequest):
        """Handle NCERT PDF ingestion with preserved RAG workflow"""
        try:
            result = await ingest_ncert_pdfs(req.paths)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    async def ncert_ingest_status():
        """Get NCERT ingestion status - always reflect current in-memory status"""
        return await get_ingest_status()

    @staticmethod
    async def ncert_qa(req: QARequest):
        """Handle NCERT Q&A with vector similarity search"""
        if not is_pinecone_available():
            raise HTTPException(503, "Pinecone unavailable")
        try:
            qvec = await generate_embedding(req.query)
            filters: Dict[str, Any] = {"board": "CBSE"}
            if req.grade:
                filters["grade_level"] = req.grade
            if req.subject:
                filters["subject"] = req.subject
            results = await query_vectors(
                index_name="educational_content_ncert",
                query_vector=qvec,
                top_k=min(max(req.top_k, 1), 12),
                filter_dict=filters,
                include_metadata=True,
            )
            citations = []
            for r in results:
                md = r.get("metadata", {})
                citations.append({
                    "file_path": md.get("file_path"),
                    "grade_level": md.get("grade_level"),
                    "chapter": md.get("chapter"),
                    "page_start": md.get("page_start"),
                    "score": r.get("score"),
                })
            # Return only citations and raw snippets to keep strictly grounded; composing answer can be a client concern
            return {
                "query": req.query,
                "top_k": req.top_k,
                "citations": citations,
            }
        except Exception as e:
            raise HTTPException(500, str(e))

    @staticmethod
    async def ncert_ingest_all():
        """Handle full NCERT ingestion - no paths provided means crawl entire CBSE/ per PRD"""
        try:
            # No paths provided => crawl entire CBSE/ per PRD
            result = await ingest_ncert_pdfs(None)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def _earlier_grades(grade: str) -> List[str]:
        """Helper to get earlier grades for prerequisite discovery"""
        # Expect format like 'grade_10'
        try:
            level = int(grade.split("_")[-1])
        except Exception:
            return []
        return [f"grade_{g}" for g in range(1, max(level, 1))]

    @staticmethod
    async def ncert_prerequisites(req: PrereqRequest):
        """Handle prerequisite discovery with vector search and floor-wise fallback"""
        if not is_pinecone_available():
            raise HTTPException(503, "Pinecone unavailable")
        try:
            qvec = await generate_embedding(req.topic)
            floors: Dict[str, List[Dict[str, Any]]] = {}
            grades = set(RagController._earlier_grades(req.grade))
            # Query without grade filter; we will group by grade in results
            filters: Dict[str, Any] = {"board": "CBSE"}
            if req.subject:
                filters["subject"] = req.subject
            results = await query_vectors(
                index_name="educational_content_ncert",
                query_vector=qvec,
                top_k=min(max(req.top_k, 1), 64),
                filter_dict=filters,
                include_metadata=True,
            )

            for r in results:
                md = r.get("metadata", {})
                g = (md.get("grade_level") or "unknown").lower()
                # Keep only earlier grades strictly below current
                if g in grades:
                    floors.setdefault(g, []).append({
                        "chapter": md.get("chapter"),
                        "file_path": md.get("file_path"),
                        "page_start": md.get("page_start"),
                        "score": r.get("score"),
                    })

            # Sort floors from closest prior grade downwards
            def grade_key(k: str) -> int:
                try:
                    return int(k.split("_")[-1])
                except Exception:
                    return -1

            ordered = []
            for g in sorted(floors.keys(), key=grade_key, reverse=True):
                ordered.append({
                    "grade_level": g,
                    "topics": floors[g][:5],
                    "estimated_duration_hours": max(1, len(floors[g]) // 2),
                    "mastery_threshold": 0.8,
                })

            if ordered:
                return {
                    "topic": req.topic,
                    "current_grade": req.grade,
                    "subject": req.subject,
                    "prerequisite_floors": ordered,
                    "discovery_method": "vector_search"
                }

            # Fallback to structured floor-wise discovery from PRD if no earlier grades present
            fallback = await discover_floor_wise_prerequisites(
                gap_code=req.topic,
                current_grade=req.grade,
                subject=req.subject,
                max_grade_levels=3,
            )
            return fallback
        except Exception as e:
            raise HTTPException(500, str(e))