"""
Vector Data Pipeline for RAG System
Extracts and vectorizes educational content from MongoDB collections for blazing fast retrieval.
"""

import os
import asyncio
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import anyio
from bson import ObjectId

from core.services.ai.pinecone_client import get_pinecone_client, generate_embedding, upsert_vectors
from core.services.ai.vector_schemas import (
    EducationalContentMetadata, LearningGapMetadata, PrerequisiteMetadata, QuestionMetadata,
    ContentType, GapType, Subject, GradeLevel, DifficultyLevel,
    extract_educational_content_metadata, extract_question_metadata, extract_remediation_metadata
)
from core.services.db_operations.base import (
    lessons_collection, question_bank_collection, student_reports_collection,
    sessions_collection, prerequisite_cache_collection
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorDataPipeline:
    """
    High-performance pipeline for extracting and vectorizing educational content.
    Optimized for blazing fast processing with Gemini embeddings.
    """
    
    def __init__(self):
        self.pinecone_client = get_pinecone_client()
        self.batch_size = 50  # Optimized batch size for speed
        self.processed_count = 0
        self.error_count = 0
        
    async def process_all_collections(self) -> Dict[str, Any]:
        """
        Process all MongoDB collections and populate Pinecone indexes.
        Returns processing statistics.
        """
        logger.info("🚀 Starting vector data pipeline processing...")
        
        results = {
            "educational_content": await self._process_educational_content(),
            "questions": await self._process_questions(),
            "remediation_data": await self._process_remediation_data(),
            "prerequisites": await self._process_prerequisites(),
            "total_processed": self.processed_count,
            "total_errors": self.error_count
        }
        
        logger.info(f"✅ Pipeline completed! Processed: {self.processed_count}, Errors: {self.error_count}")
        return results
    
    async def _process_educational_content(self) -> Dict[str, Any]:
        """Process lesson scripts and educational content."""
        logger.info("📚 Processing educational content...")
        
        try:
            def _get_lessons():
                return list(lessons_collection.find({}, {
                    "_id": 1, "chapterName": 1, "period": 1, "script": 1, 
                    "lessonScript": 1, "subject": 1, "grade": 1, "board": 1
                }))
            
            lessons = await anyio.to_thread.run_sync(_get_lessons)
            logger.info(f"Found {len(lessons)} lesson documents")
            
            vectors = []
            for lesson in lessons:
                try:
                    # Extract metadata
                    metadata = extract_educational_content_metadata(lesson)
                    
                    # Create content text for embedding
                    content_text = self._extract_lesson_content(lesson)
                    if not content_text:
                        continue
                    
                    # Generate embedding
                    embedding = await generate_embedding(content_text)
                    
                    # Create vector entry
                    vector_entry = {
                        "id": f"lesson_{lesson['_id']}",
                        "values": embedding,
                        "metadata": metadata.model_dump()
                    }
                    vectors.append(vector_entry)
                    
                    # Process in batches for speed
                    if len(vectors) >= self.batch_size:
                        await self._upsert_batch("educational_content", vectors)
                        vectors = []
                        
                except Exception as e:
                    logger.error(f"Error processing lesson {lesson.get('_id')}: {e}")
                    self.error_count += 1
            
            # Process remaining vectors
            if vectors:
                await self._upsert_batch("educational_content", vectors)
            
            self.processed_count += len(lessons)
            return {"processed": len(lessons), "errors": self.error_count}
            
        except Exception as e:
            logger.error(f"Error processing educational content: {e}")
            return {"processed": 0, "errors": 1}
    
    async def _process_questions(self) -> Dict[str, Any]:
        """Process question bank for vectorization."""
        logger.info("❓ Processing question bank...")
        
        try:
            def _get_questions():
                return list(question_bank_collection.find({}, {
                    "_id": 1, "questionText": 1, "questionType": 1, "answer": 1,
                    "explanation": 1, "difficulty": 1, "grade": 1, "topics": 1,
                    "learningOutcomes": 1, "subject": 1, "statistics": 1
                }))
            
            questions = await anyio.to_thread.run_sync(_get_questions)
            logger.info(f"Found {len(questions)} question documents")
            
            vectors = []
            for question in questions:
                try:
                    # Extract metadata
                    metadata = extract_question_metadata(question)
                    
                    # Create content text for embedding
                    content_text = self._extract_question_content(question)
                    if not content_text:
                        continue
                    
                    # Generate embedding
                    embedding = await generate_embedding(content_text)
                    
                    # Create vector entry
                    vector_entry = {
                        "id": f"question_{question['_id']}",
                        "values": embedding,
                        "metadata": metadata.model_dump()
                    }
                    vectors.append(vector_entry)
                    
                    # Process in batches for speed
                    if len(vectors) >= self.batch_size:
                        await self._upsert_batch("educational_content", vectors)
                        vectors = []
                        
                except Exception as e:
                    logger.error(f"Error processing question {question.get('_id')}: {e}")
                    self.error_count += 1
            
            # Process remaining vectors
            if vectors:
                await self._upsert_batch("educational_content", vectors)
            
            self.processed_count += len(questions)
            return {"processed": len(questions), "errors": self.error_count}
            
        except Exception as e:
            logger.error(f"Error processing questions: {e}")
            return {"processed": 0, "errors": 1}
    
    async def _process_remediation_data(self) -> Dict[str, Any]:
        """Process successful remediation cases from student reports."""
        logger.info("🔧 Processing remediation data...")
        
        try:
            def _get_reports():
                return list(student_reports_collection.find({
                    "report.remedy_report": {"$exists": True, "$ne": []}
                }, {
                    "_id": 1, "studentId": 1, "report.remedy_report": 1,
                    "classId": 1, "teacherId": 1
                }))
            
            reports = await anyio.to_thread.run_sync(_get_reports)
            logger.info(f"Found {len(reports)} student reports with remediation data")
            
            vectors = []
            for report in reports:
                try:
                    remedy_reports = report.get("report", {}).get("remedy_report", [])
                    
                    for remedy_entry in remedy_reports:
                        # Extract metadata
                        metadata = extract_remediation_metadata(remedy_entry, report)
                        
                        # Create content text for embedding
                        content_text = self._extract_remediation_content(remedy_entry)
                        if not content_text:
                            continue
                        
                        # Generate embedding
                        embedding = await generate_embedding(content_text)
                        
                        # Create vector entry
                        vector_entry = {
                            "id": f"remedy_{report['_id']}_{remedy_entry.get('timestamp', 'unknown')}",
                            "values": embedding,
                            "metadata": metadata.model_dump()
                        }
                        vectors.append(vector_entry)
                        
                        # Process in batches for speed
                        if len(vectors) >= self.batch_size:
                            await self._upsert_batch("learning_gaps", vectors)
                            vectors = []
                            
                except Exception as e:
                    logger.error(f"Error processing report {report.get('_id')}: {e}")
                    self.error_count += 1
            
            # Process remaining vectors
            if vectors:
                await self._upsert_batch("learning_gaps", vectors)
            
            self.processed_count += len(reports)
            return {"processed": len(reports), "errors": self.error_count}
            
        except Exception as e:
            logger.error(f"Error processing remediation data: {e}")
            return {"processed": 0, "errors": 1}
    
    async def _process_prerequisites(self) -> Dict[str, Any]:
        """Process prerequisite cache data."""
        logger.info("🔗 Processing prerequisite data...")
        
        try:
            def _get_prerequisites():
                return list(prerequisite_cache_collection.find({}, {
                    "_id": 1, "gap_code": 1, "grade_level": 1, "subject": 1,
                    "prerequisites": 1, "created_at": 1
                }))
            
            prerequisites = await anyio.to_thread.run_sync(_get_prerequisites)
            logger.info(f"Found {len(prerequisites)} prerequisite documents")
            
            vectors = []
            for prereq_doc in prerequisites:
                try:
                    # Create content text for embedding
                    content_text = self._extract_prerequisite_content(prereq_doc)
                    if not content_text:
                        continue
                    
                    # Create metadata
                    metadata = PrerequisiteMetadata(
                        content_type=ContentType.CURRICULUM,
                        subject=Subject.SCIENCE,  # Default, could be extracted
                        grade_level=GradeLevel.GRADE_10,  # Default, could be extracted
                        difficulty=DifficultyLevel.MEDIUM,
                        created_at=datetime.utcnow().isoformat(),
                        updated_at=datetime.utcnow().isoformat(),
                        mongo_id=str(prereq_doc["_id"]),
                        prerequisite_topic=prereq_doc.get("gap_code", "unknown"),
                        target_topics=[p.get("topic", "") for p in prereq_doc.get("prerequisites", [])],
                        priority=1,
                        estimated_duration_hours=2.0,
                        learning_objectives=[],
                        assessment_criteria=[],
                        common_misconceptions=[],
                        teaching_strategies=[],
                        prerequisite_chain=[]
                    )
                    
                    # Generate embedding
                    embedding = await generate_embedding(content_text)
                    
                    # Create vector entry
                    vector_entry = {
                        "id": f"prereq_{prereq_doc['_id']}",
                        "values": embedding,
                        "metadata": metadata.model_dump()
                    }
                    vectors.append(vector_entry)
                    
                    # Process in batches for speed
                    if len(vectors) >= self.batch_size:
                        await self._upsert_batch("prerequisites", vectors)
                        vectors = []
                        
                except Exception as e:
                    logger.error(f"Error processing prerequisite {prereq_doc.get('_id')}: {e}")
                    self.error_count += 1
            
            # Process remaining vectors
            if vectors:
                await self._upsert_batch("prerequisites", vectors)
            
            self.processed_count += len(prerequisites)
            return {"processed": len(prerequisites), "errors": self.error_count}
            
        except Exception as e:
            logger.error(f"Error processing prerequisites: {e}")
            return {"processed": 0, "errors": 1}
    
    def _extract_lesson_content(self, lesson: Dict[str, Any]) -> str:
        """Extract text content from lesson for embedding."""
        content_parts = []
        
        # Add chapter and period info
        if lesson.get("chapterName"):
            content_parts.append(f"Chapter: {lesson['chapterName']}")
        if lesson.get("period"):
            content_parts.append(f"Period: {lesson['period']}")
        
        # Extract script content
        script = lesson.get("script") or lesson.get("lessonScript")
        if script:
            if isinstance(script, dict):
                # Extract text from script structure
                for key, value in script.items():
                    if isinstance(value, str) and value.strip():
                        content_parts.append(value.strip())
            elif isinstance(script, str) and script.strip():
                content_parts.append(script.strip())
        
        return " ".join(content_parts) if content_parts else ""
    
    def _extract_question_content(self, question: Dict[str, Any]) -> str:
        """Extract text content from question for embedding."""
        content_parts = []
        
        # Add question text
        if question.get("questionText"):
            content_parts.append(question["questionText"])
        
        # Add explanation
        if question.get("explanation"):
            content_parts.append(question["explanation"])
        
        # Add topics
        if question.get("topics"):
            content_parts.append(f"Topics: {', '.join(question['topics'])}")
        
        # Add learning outcomes
        if question.get("learningOutcomes"):
            content_parts.append(f"Learning outcomes: {', '.join(question['learningOutcomes'])}")
        
        return " ".join(content_parts) if content_parts else ""
    
    def _extract_remediation_content(self, remedy_entry: Dict[str, Any]) -> str:
        """Extract text content from remediation entry for embedding."""
        content_parts = []
        
        # Add gap information
        if remedy_entry.get("gap_code"):
            content_parts.append(f"Gap: {remedy_entry['gap_code']}")
        
        # Add artifact content
        artifact = remedy_entry.get("artifact", {})
        if artifact:
            for key, value in artifact.items():
                if isinstance(value, str) and value.strip():
                    content_parts.append(value.strip())
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str) and item.strip():
                            content_parts.append(item.strip())
        
        return " ".join(content_parts) if content_parts else ""
    
    def _extract_prerequisite_content(self, prereq_doc: Dict[str, Any]) -> str:
        """Extract text content from prerequisite document for embedding."""
        content_parts = []
        
        # Add gap code
        if prereq_doc.get("gap_code"):
            content_parts.append(f"Gap: {prereq_doc['gap_code']}")
        
        # Add prerequisites
        prerequisites = prereq_doc.get("prerequisites", [])
        for prereq in prerequisites:
            if isinstance(prereq, dict) and prereq.get("topic"):
                content_parts.append(f"Prerequisite: {prereq['topic']}")
            elif isinstance(prereq, str):
                content_parts.append(f"Prerequisite: {prereq}")
        
        return " ".join(content_parts) if content_parts else ""
    
    async def _upsert_batch(self, index_name: str, vectors: List[Dict[str, Any]]) -> None:
        """Upsert a batch of vectors to Pinecone."""
        try:
            success = await upsert_vectors(index_name, vectors)
            if success:
                logger.info(f"✅ Upserted {len(vectors)} vectors to {index_name}")
            else:
                logger.error(f"❌ Failed to upsert {len(vectors)} vectors to {index_name}")
                self.error_count += len(vectors)
        except Exception as e:
            logger.error(f"❌ Error upserting batch to {index_name}: {e}")
            self.error_count += len(vectors)

# Convenience function for easy access
async def run_vector_data_pipeline() -> Dict[str, Any]:
    """Run the complete vector data pipeline."""
    pipeline = VectorDataPipeline()
    return await pipeline.process_all_collections()
