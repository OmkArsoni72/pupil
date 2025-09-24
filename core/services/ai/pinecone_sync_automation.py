"""
Pinecone Sync/Update Automation for RAG System
Detects new or updated content in MongoDB collections and automatically syncs to Pinecone indexes.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
import anyio
from bson import ObjectId

from core.services.ai.pinecone_client import (
    get_pinecone_client, generate_embedding, upsert_vectors, is_pinecone_available
)
from core.services.ai.vector_schemas import (
    extract_educational_content_metadata, extract_question_metadata, extract_remediation_metadata,
    EducationalContentMetadata, QuestionMetadata, LearningGapMetadata
)
from core.services.db_operations.base import (
    sessions_collection, lesson_script_collection, question_bank_collection,
    student_reports_collection, pinecone_sync_log_collection
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PineconeSyncAutomation:
    """
    Automated sync system for keeping Pinecone indexes up-to-date with MongoDB collections.
    """
    
    def __init__(self):
        self.pinecone_available = is_pinecone_available()
        self.sync_interval_minutes = 15  # Sync every 15 minutes
        self.batch_size = 50
        self.last_sync_times = {
            "sessions": datetime.utcnow() - timedelta(hours=1),
            "lesson_script": datetime.utcnow() - timedelta(hours=1),
            "question_bank": datetime.utcnow() - timedelta(hours=1),
            "student_reports": datetime.utcnow() - timedelta(hours=1)
        }
        self.sync_running = False
        
        logger.info(f"Pinecone Sync Automation initialized. Pinecone available: {self.pinecone_available}")
    
    async def start_automated_sync(self):
        """
        Start the automated sync process.
        """
        if not self.pinecone_available:
            logger.warning("Pinecone not available - sync automation disabled")
            return
        
        if self.sync_running:
            logger.info("Sync automation already running")
            return
        
        self.sync_running = True
        logger.info("🚀 Starting Pinecone sync automation")
        
        try:
            while self.sync_running:
                await self._perform_sync_cycle()
                await asyncio.sleep(self.sync_interval_minutes * 60)
        except Exception as e:
            logger.error(f"❌ Sync automation failed: {e}")
        finally:
            self.sync_running = False
            logger.info("🛑 Pinecone sync automation stopped")
    
    async def stop_automated_sync(self):
        """
        Stop the automated sync process.
        """
        self.sync_running = False
        logger.info("🛑 Stopping Pinecone sync automation")
    
    async def trigger_manual_sync(self, collection_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Trigger manual sync for specific collection or all collections.
        """
        logger.info(f"🔄 Triggering manual sync for: {collection_name or 'all collections'}")
        
        if not self.pinecone_available:
            return {"error": "Pinecone not available"}
        
        sync_results = {}
        
        if collection_name:
            sync_results[collection_name] = await self._sync_collection(collection_name)
        else:
            # Sync all collections
            for collection in self.last_sync_times.keys():
                sync_results[collection] = await self._sync_collection(collection)
        
        return sync_results
    
    async def _perform_sync_cycle(self):
        """
        Perform one sync cycle for all collections.
        """
        logger.info("🔄 Starting sync cycle")
        
        sync_results = {}
        for collection_name in self.last_sync_times.keys():
            try:
                result = await self._sync_collection(collection_name)
                sync_results[collection_name] = result
            except Exception as e:
                logger.error(f"❌ Failed to sync {collection_name}: {e}")
                sync_results[collection_name] = {"error": str(e)}
        
        # Log sync cycle results
        await self._log_sync_cycle(sync_results)
        
        logger.info("✅ Sync cycle completed")
    
    async def _sync_collection(self, collection_name: str) -> Dict[str, Any]:
        """
        Sync a specific collection to Pinecone.
        """
        logger.info(f"🔄 Syncing collection: {collection_name}")
        
        last_sync = self.last_sync_times[collection_name]
        current_sync = datetime.utcnow()
        
        # Get new/updated documents since last sync
        new_documents = await self._get_updated_documents(collection_name, last_sync)
        
        if not new_documents:
            logger.info(f"📭 No new documents in {collection_name}")
            self.last_sync_times[collection_name] = current_sync
            return {"documents_processed": 0, "vectors_upserted": 0}
        
        logger.info(f"📄 Found {len(new_documents)} new/updated documents in {collection_name}")
        
        # Process documents in batches
        vectors_upserted = 0
        processed_documents = 0
        
        for i in range(0, len(new_documents), self.batch_size):
            batch = new_documents[i:i + self.batch_size]
            
            try:
                # Convert documents to vectors
                vectors = await self._convert_documents_to_vectors(collection_name, batch)
                
                if vectors:
                    # Upsert vectors to Pinecone
                    index_name = self._get_index_name_for_collection(collection_name)
                    success = await upsert_vectors(index_name, vectors)
                    
                    if success:
                        vectors_upserted += len(vectors)
                        processed_documents += len(batch)
                        logger.info(f"✅ Upserted {len(vectors)} vectors from {len(batch)} documents")
                    else:
                        logger.error(f"❌ Failed to upsert vectors for batch")
                else:
                    logger.warning(f"⚠️ No vectors generated for batch")
                    
            except Exception as e:
                logger.error(f"❌ Failed to process batch: {e}")
        
        # Update last sync time
        self.last_sync_times[collection_name] = current_sync
        
        result = {
            "documents_processed": processed_documents,
            "vectors_upserted": vectors_upserted,
            "sync_time": current_sync.isoformat()
        }
        
        logger.info(f"✅ Collection {collection_name} sync completed: {result}")
        return result
    
    async def _get_updated_documents(self, collection_name: str, since: datetime) -> List[Dict[str, Any]]:
        """
        Get documents updated since the last sync time.
        """
        collection = self._get_collection(collection_name)
        if not collection:
            return []
        
        try:
            # Query for documents updated since last sync
            query = {
                "$or": [
                    {"updated_at": {"$gt": since}},
                    {"created_at": {"$gt": since}},
                    # For documents without timestamp fields, check if they exist
                    {"updated_at": {"$exists": False}, "created_at": {"$exists": False}}
                ]
            }
            
            def _find_documents():
                return list(collection.find(query).limit(1000))  # Limit to prevent memory issues
            
            documents = await anyio.to_thread.run_sync(_find_documents)
            
            # Convert ObjectId to string for JSON serialization
            for doc in documents:
                if "_id" in doc:
                    doc["_id"] = str(doc["_id"])
            
            return documents
            
        except Exception as e:
            logger.error(f"❌ Failed to get updated documents from {collection_name}: {e}")
            return []
    
    async def _convert_documents_to_vectors(
        self,
        collection_name: str,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Convert documents to vector format for Pinecone.
        """
        vectors = []
        
        for doc in documents:
            try:
                vector_data = await self._convert_document_to_vector(collection_name, doc)
                if vector_data:
                    vectors.append(vector_data)
            except Exception as e:
                logger.error(f"❌ Failed to convert document to vector: {e}")
                continue
        
        return vectors
    
    async def _convert_document_to_vector(
        self,
        collection_name: str,
        document: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Convert a single document to vector format.
        """
        try:
            # Extract content and metadata based on collection type
            if collection_name == "sessions":
                return await self._convert_session_to_vector(document)
            elif collection_name == "lesson_script":
                return await self._convert_lesson_script_to_vector(document)
            elif collection_name == "question_bank":
                return await self._convert_question_to_vector(document)
            elif collection_name == "student_reports":
                return await self._convert_remedy_report_to_vector(document)
            else:
                logger.warning(f"⚠️ Unknown collection type: {collection_name}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to convert document: {e}")
            return None
    
    async def _convert_session_to_vector(self, session: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert session document to vector format.
        """
        try:
            # Extract lesson script content
            lesson_script = session.get("lessonScript", {})
            if not lesson_script:
                return None
            
            # Extract text content for embedding
            content_text = self._extract_lesson_script_text(lesson_script)
            if not content_text:
                return None
            
            # Generate embedding
            embedding = await generate_embedding(content_text)
            
            # Create metadata
            metadata = extract_educational_content_metadata(session)
            
            return {
                "id": f"session_{session['_id']}",
                "vector": embedding,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to convert session to vector: {e}")
            return None
    
    async def _convert_lesson_script_to_vector(self, lesson: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert lesson script document to vector format.
        """
        try:
            # Extract text content
            content_text = self._extract_lesson_script_text(lesson)
            if not content_text:
                return None
            
            # Generate embedding
            embedding = await generate_embedding(content_text)
            
            # Create metadata
            metadata = extract_educational_content_metadata(lesson)
            
            return {
                "id": f"lesson_{lesson['_id']}",
                "vector": embedding,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to convert lesson script to vector: {e}")
            return None
    
    async def _convert_question_to_vector(self, question: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert question document to vector format.
        """
        try:
            # Extract question text
            question_text = question.get("questionText", "")
            if not question_text:
                return None
            
            # Generate embedding
            embedding = await generate_embedding(question_text)
            
            # Create metadata
            metadata = extract_question_metadata(question)
            
            return {
                "id": f"question_{question['_id']}",
                "vector": embedding,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to convert question to vector: {e}")
            return None
    
    async def _convert_remedy_report_to_vector(self, report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Convert remedy report document to vector format.
        """
        try:
            # Extract remedy report entries
            remedy_report = report.get("report", {}).get("remedy_report", [])
            if not remedy_report:
                return None
            
            # Process each remedy entry
            vectors = []
            for i, entry in enumerate(remedy_report):
                try:
                    # Extract content from remedy entry
                    content_text = self._extract_remedy_entry_text(entry)
                    if not content_text:
                        continue
                    
                    # Generate embedding
                    embedding = await generate_embedding(content_text)
                    
                    # Create metadata
                    metadata = extract_remediation_metadata(entry)
                    metadata["student_id"] = report.get("studentId", "")
                    metadata["class_id"] = report.get("classId", "")
                    
                    vectors.append({
                        "id": f"remedy_{report['_id']}_{i}",
                        "vector": embedding,
                        "metadata": metadata
                    })
                    
                except Exception as e:
                    logger.error(f"❌ Failed to convert remedy entry to vector: {e}")
                    continue
            
            return vectors[0] if vectors else None  # Return first vector for now
            
        except Exception as e:
            logger.error(f"❌ Failed to convert remedy report to vector: {e}")
            return None
    
    def _extract_lesson_script_text(self, lesson_script: Dict[str, Any]) -> str:
        """
        Extract text content from lesson script.
        """
        text_parts = []
        
        # Extract from different possible structures
        if isinstance(lesson_script, dict):
            # Try common fields
            for field in ["content", "text", "script", "lessonScript", "sections"]:
                if field in lesson_script:
                    content = lesson_script[field]
                    if isinstance(content, str):
                        text_parts.append(content)
                    elif isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and "text" in item:
                                text_parts.append(item["text"])
                            elif isinstance(item, str):
                                text_parts.append(item)
                    elif isinstance(content, dict):
                        text_parts.append(str(content))
        
        return " ".join(text_parts)
    
    def _extract_remedy_entry_text(self, entry: Dict[str, Any]) -> str:
        """
        Extract text content from remedy entry.
        """
        text_parts = []
        
        # Extract from artifact
        artifact = entry.get("artifact", {})
        if isinstance(artifact, dict):
            for field in ["content", "text", "summary", "description"]:
                if field in artifact:
                    text_parts.append(str(artifact[field]))
        
        # Extract gap information
        gap_code = entry.get("gap_code", "")
        if gap_code:
            text_parts.append(f"Gap: {gap_code}")
        
        return " ".join(text_parts)
    
    def _get_collection(self, collection_name: str):
        """
        Get MongoDB collection by name.
        """
        collection_map = {
            "sessions": sessions_collection,
            "lesson_script": lesson_script_collection,
            "question_bank": question_bank_collection,
            "student_reports": student_reports_collection
        }
        return collection_map.get(collection_name)
    
    def _get_index_name_for_collection(self, collection_name: str) -> str:
        """
        Get Pinecone index name for collection.
        """
        index_map = {
            "sessions": "educational_content",
            "lesson_script": "educational_content",
            "question_bank": "educational_content",
            "student_reports": "learning_gaps"
        }
        return index_map.get(collection_name, "educational_content")
    
    async def _log_sync_cycle(self, sync_results: Dict[str, Any]) -> None:
        """
        Log sync cycle results to database.
        """
        try:
            def _insert():
                return pinecone_sync_log_collection.insert_one({
                    "sync_cycle_id": f"SYNC_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    "sync_results": sync_results,
                    "total_documents_processed": sum(
                        result.get("documents_processed", 0) for result in sync_results.values()
                        if isinstance(result, dict)
                    ),
                    "total_vectors_upserted": sum(
                        result.get("vectors_upserted", 0) for result in sync_results.values()
                        if isinstance(result, dict)
                    ),
                    "sync_timestamp": datetime.utcnow().isoformat()
                })
            await anyio.to_thread.run_sync(_insert)
        except Exception as e:
            logger.warning(f"⚠️ Failed to log sync cycle: {e}")

# Global instance
pinecone_sync_automation = PineconeSyncAutomation()

# Convenience functions
async def start_pinecone_sync_automation():
    """Start the automated Pinecone sync process."""
    await pinecone_sync_automation.start_automated_sync()

async def stop_pinecone_sync_automation():
    """Stop the automated Pinecone sync process."""
    await pinecone_sync_automation.stop_automated_sync()

async def trigger_manual_pinecone_sync(collection_name: Optional[str] = None) -> Dict[str, Any]:
    """Trigger manual sync for specific collection or all collections."""
    return await pinecone_sync_automation.trigger_manual_sync(collection_name)
