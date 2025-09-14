#!/usr/bin/env python3
"""
Working Vector Data Pipeline for RAG System
Fixes the metadata extraction issues and properly populates Pinecone indexes.
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class WorkingVectorPipeline:
    """
    A working vector data pipeline that properly extracts and vectorizes content.
    """
    
    def __init__(self):
        self.pinecone_available = False
        self.gemini_available = False
        self._check_availability()
    
    def _check_availability(self):
        """Check if required services are available."""
        try:
            from services.ai.pinecone_client import is_pinecone_available
            from services.ai.pinecone_client import generate_embedding
            
            self.pinecone_available = is_pinecone_available()
            self.gemini_available = bool(os.getenv("GEMINI_API_KEY"))
            
            logger.info(f"Pinecone available: {self.pinecone_available}")
            logger.info(f"Gemini available: {self.gemini_available}")
            
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
    
    async def process_all_collections(self) -> Dict[str, Any]:
        """
        Process all MongoDB collections and populate Pinecone indexes.
        """
        if not self.pinecone_available or not self.gemini_available:
            logger.error("Required services not available")
            return {"error": "Services not available"}
        
        logger.info("🚀 Starting vector data pipeline...")
        
        results = {
            "educational_content": await self._process_educational_content(),
            "learning_gaps": await self._process_learning_gaps(),
            "prerequisites": await self._process_prerequisites(),
            "total_processed": 0,
            "total_errors": 0
        }
        
        # Calculate totals
        for key, value in results.items():
            if isinstance(value, dict):
                results["total_processed"] += value.get("processed", 0)
                results["total_errors"] += value.get("errors", 0)
        
        logger.info(f"✅ Pipeline completed! Processed: {results['total_processed']}, Errors: {results['total_errors']}")
        return results
    
    async def _process_educational_content(self) -> Dict[str, Any]:
        """Process educational content (sessions and question bank)."""
        logger.info("📚 Processing educational content...")
        
        try:
            from services.db_operations.base import sessions_collection, question_bank_collection
            from services.ai.pinecone_client import generate_embedding, upsert_vectors
            
            processed = 0
            errors = 0
            
            # Process sessions (lesson scripts)
            logger.info("📖 Processing sessions (lesson scripts)...")
            sessions = list(sessions_collection.find({}))
            logger.info(f"Found {len(sessions)} session documents")
            
            session_vectors = []
            for session in sessions:
                try:
                    vector_data = await self._create_session_vector(session)
                    if vector_data:
                        session_vectors.append(vector_data)
                        processed += 1
                except Exception as e:
                    logger.error(f"Error processing session {session.get('_id')}: {e}")
                    errors += 1
            
            # Process question bank
            logger.info("❓ Processing question bank...")
            questions = list(question_bank_collection.find({}))
            logger.info(f"Found {len(questions)} question documents")
            
            question_vectors = []
            for question in questions:
                try:
                    vector_data = await self._create_question_vector(question)
                    if vector_data:
                        question_vectors.append(vector_data)
                        processed += 1
                except Exception as e:
                    logger.error(f"Error processing question {question.get('_id')}: {e}")
                    errors += 1
            
            # Upsert to educational-content index
            all_vectors = session_vectors + question_vectors
            if all_vectors:
                await upsert_vectors("educational-content", all_vectors)
                logger.info(f"✅ Upserted {len(all_vectors)} vectors to educational-content")
            
            return {"processed": processed, "errors": errors}
            
        except Exception as e:
            logger.error(f"Error processing educational content: {e}")
            return {"processed": 0, "errors": 1}
    
    async def _process_learning_gaps(self) -> Dict[str, Any]:
        """Process learning gaps from student reports."""
        logger.info("🎯 Processing learning gaps...")
        
        try:
            from services.db_operations.base import student_reports_collection
            from services.ai.pinecone_client import generate_embedding, upsert_vectors
            
            processed = 0
            errors = 0
            
            reports = list(student_reports_collection.find({}))
            logger.info(f"Found {len(reports)} student report documents")
            
            gap_vectors = []
            for report in reports:
                try:
                    # Extract remedy reports
                    remedy_reports = report.get("report", {}).get("remedy_report", [])
                    for remedy_entry in remedy_reports:
                        vector_data = await self._create_remedy_vector(remedy_entry, report)
                        if vector_data:
                            gap_vectors.append(vector_data)
                            processed += 1
                except Exception as e:
                    logger.error(f"Error processing report {report.get('_id')}: {e}")
                    errors += 1
            
            # Upsert to learning-gaps index
            if gap_vectors:
                await upsert_vectors("learning-gaps", gap_vectors)
                logger.info(f"✅ Upserted {len(gap_vectors)} vectors to learning-gaps")
            
            return {"processed": processed, "errors": errors}
            
        except Exception as e:
            logger.error(f"Error processing learning gaps: {e}")
            return {"processed": 0, "errors": 1}
    
    async def _process_prerequisites(self) -> Dict[str, Any]:
        """Process prerequisite cache."""
        logger.info("🔗 Processing prerequisites...")
        
        try:
            from services.db_operations.base import prerequisite_cache_collection
            from services.ai.pinecone_client import generate_embedding, upsert_vectors
            
            processed = 0
            errors = 0
            
            prerequisites = list(prerequisite_cache_collection.find({}))
            logger.info(f"Found {len(prerequisites)} prerequisite documents")
            
            prereq_vectors = []
            for prereq in prerequisites:
                try:
                    vector_data = await self._create_prerequisite_vector(prereq)
                    if vector_data:
                        prereq_vectors.append(vector_data)
                        processed += 1
                except Exception as e:
                    logger.error(f"Error processing prerequisite {prereq.get('_id')}: {e}")
                    errors += 1
            
            # Upsert to prerequisites index
            if prereq_vectors:
                await upsert_vectors("prerequisites", prereq_vectors)
                logger.info(f"✅ Upserted {len(prereq_vectors)} vectors to prerequisites")
            
            return {"processed": processed, "errors": errors}
            
        except Exception as e:
            logger.error(f"Error processing prerequisites: {e}")
            return {"processed": 0, "errors": 1}
    
    async def _create_session_vector(self, session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create vector for session (lesson script)."""
        try:
            from services.ai.pinecone_client import generate_embedding
            
            # Extract content
            content_parts = []
            
            # Session title
            if session.get("sessionTitle"):
                content_parts.append(f"Session: {session['sessionTitle']}")
            
            # Lesson script content
            lesson_script = session.get("lessonScript", {})
            if lesson_script and isinstance(lesson_script, dict):
                script_content = lesson_script.get("scriptContent", "")
                if script_content:
                    content_parts.append(script_content)
            
            # Learning outcomes
            learning_outcomes = session.get("learningOutcomes", [])
            if learning_outcomes:
                content_parts.append(f"Learning outcomes: {', '.join(learning_outcomes)}")
            
            if not content_parts:
                return None
            
            content_text = " ".join(content_parts)
            
            # Generate embedding
            embedding = await generate_embedding(content_text)
            
            # Create metadata
            metadata = {
                "content_type": "lesson_script",
                "subject": "general",  # Could be extracted from session data
                "grade_level": "grade_10",  # Could be extracted from session data
                "difficulty": "medium",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "mongo_id": str(session["_id"]),
                "topic": session.get("sessionTitle", "Unknown"),
                "chapter": session.get("chapterId", ""),
                "period": str(session.get("lessonNumber", "")),
                "content_text": content_text,
                "learning_objectives": learning_outcomes,
                "prerequisites": [],
                "keywords": learning_outcomes,
                "success_rate": None,
                "usage_count": 0,
                "board": "CBSE",  # Default
                "language": "english"
            }
            
            return {
                "id": f"session_{session['_id']}",
                "values": embedding,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error creating session vector: {e}")
            return None
    
    async def _create_question_vector(self, question: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create vector for question."""
        try:
            from services.ai.pinecone_client import generate_embedding
            
            # Extract content
            content_parts = []
            
            # Question text
            if question.get("questionText"):
                content_parts.append(question["questionText"])
            
            # Answer explanation
            answer = question.get("answer", {})
            if isinstance(answer, dict) and answer.get("explanation"):
                content_parts.append(f"Explanation: {answer['explanation']}")
            
            # Topics
            topics = question.get("topics", [])
            if topics:
                content_parts.append(f"Topics: {', '.join(topics)}")
            
            # Learning outcomes
            learning_outcomes = question.get("learningOutcomes", [])
            if learning_outcomes:
                content_parts.append(f"Learning outcomes: {', '.join(learning_outcomes)}")
            
            if not content_parts:
                return None
            
            content_text = " ".join(content_parts)
            
            # Generate embedding
            embedding = await generate_embedding(content_text)
            
            # Create metadata
            metadata = {
                "content_type": "question",
                "subject": "general",  # Could be extracted from topics
                "grade_level": question.get("grade", "grade_10"),
                "difficulty": question.get("difficulty", "medium"),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "mongo_id": str(question["_id"]),
                "question_text": question.get("questionText", ""),
                "question_type": question.get("questionType", "MCQ"),
                "answer": answer.get("key", "") if isinstance(answer, dict) else str(answer),
                "explanation": answer.get("explanation", "") if isinstance(answer, dict) else "",
                "topics": topics,
                "learning_outcomes": learning_outcomes,
                "usage_history": question.get("usageHistory", []),
                "statistics": question.get("statistics", {}),
                "best_solution": None,
                "fastest_solution": None
            }
            
            return {
                "id": f"question_{question['_id']}",
                "values": embedding,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error creating question vector: {e}")
            return None
    
    async def _create_remedy_vector(self, remedy_entry: Dict[str, Any], report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create vector for remedy report entry."""
        try:
            from services.ai.pinecone_client import generate_embedding
            
            # Extract content
            content_parts = []
            
            # Topic
            if remedy_entry.get("topic"):
                content_parts.append(f"Topic: {remedy_entry['topic']}")
            
            # Action taken
            if remedy_entry.get("actionTaken"):
                content_parts.append(f"Action: {remedy_entry['actionTaken']}")
            
            # Outcome
            if remedy_entry.get("outcome"):
                content_parts.append(f"Outcome: {remedy_entry['outcome']}")
            
            # Learning gaps
            if remedy_entry.get("learning_gaps"):
                content_parts.append(f"Learning gaps: {remedy_entry['learning_gaps']}")
            
            # Remarks
            if remedy_entry.get("remarks"):
                content_parts.append(f"Remarks: {remedy_entry['remarks']}")
            
            if not content_parts:
                return None
            
            content_text = " ".join(content_parts)
            
            # Generate embedding
            embedding = await generate_embedding(content_text)
            
            # Create metadata
            metadata = {
                "content_type": "remediation_plan",
                "subject": "general",  # Could be extracted from topic
                "grade_level": "grade_10",  # Could be extracted from report
                "difficulty": "medium",
                "created_at": remedy_entry.get("date", datetime.utcnow().isoformat()),
                "updated_at": datetime.utcnow().isoformat(),
                "mongo_id": str(report["_id"]),
                "gap_code": remedy_entry.get("topic", "unknown"),
                "gap_type": "foundational",  # Default for remedy reports
                "evidence": [remedy_entry.get("learning_gaps", "")],
                "student_profile": f"student_{report.get('studentId', 'unknown')}",
                "successful_prerequisites": [],
                "learning_modes_used": [],
                "remediation_success_rate": None,
                "time_to_resolve_hours": None,
                "similar_gaps": [],
                "teacher_notes": remedy_entry.get("remarks", "")
            }
            
            return {
                "id": f"remedy_{report['_id']}_{remedy_entry.get('remedyId', 'unknown')}",
                "values": embedding,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error creating remedy vector: {e}")
            return None
    
    async def _create_prerequisite_vector(self, prereq: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create vector for prerequisite cache entry."""
        try:
            from services.ai.pinecone_client import generate_embedding
            
            # Extract content
            content_parts = []
            
            # Gap code
            if prereq.get("gap_code"):
                content_parts.append(f"Gap: {prereq['gap_code']}")
            
            # Prerequisites
            prerequisites = prereq.get("prerequisites", [])
            for prereq_item in prerequisites:
                if isinstance(prereq_item, str):
                    content_parts.append(f"Prerequisite: {prereq_item}")
                elif isinstance(prereq_item, dict) and prereq_item.get("topic"):
                    content_parts.append(f"Prerequisite: {prereq_item['topic']}")
            
            if not content_parts:
                return None
            
            content_text = " ".join(content_parts)
            
            # Generate embedding
            embedding = await generate_embedding(content_text)
            
            # Create metadata
            metadata = {
                "content_type": "curriculum",
                "subject": prereq.get("subject", "science"),
                "grade_level": prereq.get("grade_level", "grade_10"),
                "difficulty": "medium",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "mongo_id": str(prereq["_id"]),
                "prerequisite_topic": prereq.get("gap_code", "unknown"),
                "target_topics": [p.get("topic", "") if isinstance(p, dict) else str(p) for p in prerequisites],
                "priority": 1,
                "estimated_duration_hours": 2.0,
                "learning_objectives": [],
                "assessment_criteria": [],
                "common_misconceptions": [],
                "teaching_strategies": [],
                "prerequisite_chain": []
            }
            
            return {
                "id": f"prereq_{prereq['_id']}",
                "values": embedding,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error creating prerequisite vector: {e}")
            return None

async def main():
    """Main function to run the working vector pipeline."""
    logger.info("🚀 Starting Working Vector Data Pipeline")
    logger.info("=" * 60)
    
    # Check environment
    required_vars = ["PINECONE_API_KEY", "GEMINI_API_KEY", "MONGO_URI"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return
    
    logger.info("✅ Environment variables configured")
    
    # Run pipeline
    pipeline = WorkingVectorPipeline()
    results = await pipeline.process_all_collections()
    
    # Display results
    logger.info("\n📊 Pipeline Results:")
    logger.info("=" * 40)
    
    for key, value in results.items():
        if isinstance(value, dict) and "processed" in value:
            processed = value.get("processed", 0)
            errors = value.get("errors", 0)
            logger.info(f"  {key}: {processed} processed, {errors} errors")
        elif key in ["total_processed", "total_errors"]:
            logger.info(f"  {key}: {value}")
    
    logger.info("\n✨ Pipeline completed successfully!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n⏹️  Pipeline interrupted by user")
    except Exception as e:
        logger.error(f"\n❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
