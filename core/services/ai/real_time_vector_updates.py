"""
Real-time Vector Updates for RAG System
Handles automatic vector updates when new content is added or modified.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import anyio
from bson import ObjectId

from services.ai.pinecone_client import generate_embedding, upsert_vectors, delete_vectors
from services.ai.vector_schemas import (
    extract_educational_content_metadata, extract_question_metadata, extract_remediation_metadata
)
from services.db_operations.base import (
    lessons_collection, question_bank_collection, student_reports_collection
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RealTimeVectorUpdater:
    """
    Handles real-time vector updates for new and modified content.
    Ensures vector database stays synchronized with MongoDB.
    """
    
    def __init__(self):
        self.update_queue = asyncio.Queue()
        self.batch_size = 10
        self.batch_timeout = 5.0  # seconds
        self.processing = False
    
    async def start_processing(self):
        """Start the real-time update processing loop."""
        if self.processing:
            return
        
        self.processing = True
        logger.info("🚀 Starting real-time vector update processing")
        
        while self.processing:
            try:
                # Process updates in batches
                await self._process_batch()
            except Exception as e:
                logger.error(f"Error in real-time update processing: {e}")
                await asyncio.sleep(1)
    
    async def stop_processing(self):
        """Stop the real-time update processing loop."""
        self.processing = False
        logger.info("🛑 Stopped real-time vector update processing")
    
    async def queue_update(self, update_type: str, document_id: str, operation: str, data: Dict[str, Any]):
        """Queue a vector update operation."""
        update_item = {
            "update_type": update_type,
            "document_id": document_id,
            "operation": operation,  # "create", "update", "delete"
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.update_queue.put(update_item)
        logger.info(f"📝 Queued {operation} update for {update_type}: {document_id}")
    
    async def _process_batch(self):
        """Process a batch of updates."""
        updates = []
        start_time = asyncio.get_event_loop().time()
        
        # Collect updates until batch size or timeout
        while len(updates) < self.batch_size:
            try:
                # Wait for next update with timeout
                remaining_time = self.batch_timeout - (asyncio.get_event_loop().time() - start_time)
                if remaining_time <= 0:
                    break
                
                update = await asyncio.wait_for(self.update_queue.get(), timeout=remaining_time)
                updates.append(update)
                
            except asyncio.TimeoutError:
                break
        
        if updates:
            await self._process_updates(updates)
    
    async def _process_updates(self, updates: List[Dict[str, Any]]):
        """Process a list of updates."""
        logger.info(f"🔄 Processing {len(updates)} vector updates")
        
        # Group updates by type and operation
        grouped_updates = {}
        for update in updates:
            key = f"{update['update_type']}_{update['operation']}"
            if key not in grouped_updates:
                grouped_updates[key] = []
            grouped_updates[key].append(update)
        
        # Process each group
        for group_key, group_updates in grouped_updates.items():
            try:
                await self._process_update_group(group_key, group_updates)
            except Exception as e:
                logger.error(f"Error processing update group {group_key}: {e}")
    
    async def _process_update_group(self, group_key: str, updates: List[Dict[str, Any]]):
        """Process a group of similar updates."""
        update_type, operation = group_key.split("_", 1)
        
        if operation == "delete":
            await self._process_deletions(update_type, updates)
        else:
            await self._process_upserts(update_type, updates)
    
    async def _process_deletions(self, update_type: str, updates: List[Dict[str, Any]]):
        """Process deletion updates."""
        vector_ids = [f"{update_type}_{update['document_id']}" for update in updates]
        
        # Determine target index
        index_name = self._get_index_name(update_type)
        
        # Delete vectors
        success = await delete_vectors(index_name, vector_ids)
        if success:
            logger.info(f"✅ Deleted {len(vector_ids)} vectors from {index_name}")
        else:
            logger.error(f"❌ Failed to delete vectors from {index_name}")
    
    async def _process_upserts(self, update_type: str, updates: List[Dict[str, Any]]):
        """Process upsert updates."""
        vectors = []
        
        for update in updates:
            try:
                vector = await self._create_vector_from_update(update_type, update)
                if vector:
                    vectors.append(vector)
            except Exception as e:
                logger.error(f"Error creating vector for {update_type} {update['document_id']}: {e}")
        
        if vectors:
            # Determine target index
            index_name = self._get_index_name(update_type)
            
            # Upsert vectors
            success = await upsert_vectors(index_name, vectors)
            if success:
                logger.info(f"✅ Upserted {len(vectors)} vectors to {index_name}")
            else:
                logger.error(f"❌ Failed to upsert vectors to {index_name}")
    
    async def _create_vector_from_update(self, update_type: str, update: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Create a vector from an update."""
        document_id = update["document_id"]
        data = update["data"]
        operation = update["operation"]
        
        if operation == "delete":
            return None
        
        # Get the full document from MongoDB
        document = await self._get_document(update_type, document_id)
        if not document:
            logger.warning(f"Document not found for {update_type}: {document_id}")
            return None
        
        # Extract metadata based on type
        if update_type == "lesson":
            metadata = extract_educational_content_metadata(document)
            content_text = self._extract_lesson_content(document)
        elif update_type == "question":
            metadata = extract_question_metadata(document)
            content_text = self._extract_question_content(document)
        elif update_type == "remediation":
            metadata = extract_remediation_metadata(data, {"studentId": "unknown"})
            content_text = self._extract_remediation_content(data)
        else:
            logger.warning(f"Unknown update type: {update_type}")
            return None
        
        if not content_text:
            logger.warning(f"No content text extracted for {update_type}: {document_id}")
            return None
        
        # Generate embedding
        embedding = await generate_embedding(content_text)
        
        # Create vector entry
        return {
            "id": f"{update_type}_{document_id}",
            "values": embedding,
            "metadata": metadata.model_dump()
        }
    
    async def _get_document(self, update_type: str, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document from MongoDB."""
        try:
            if update_type == "lesson":
                def _get_lesson():
                    return lessons_collection.find_one({"_id": ObjectId(document_id)})
                return await anyio.to_thread.run_sync(_get_lesson)
            
            elif update_type == "question":
                def _get_question():
                    return question_bank_collection.find_one({"_id": ObjectId(document_id)})
                return await anyio.to_thread.run_sync(_get_question)
            
            elif update_type == "remediation":
                # For remediation, the data is already provided in the update
                return None
            
            else:
                logger.warning(f"Unknown document type: {update_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting document {update_type}:{document_id}: {e}")
            return None
    
    def _get_index_name(self, update_type: str) -> str:
        """Get the target Pinecone index name for an update type."""
        if update_type in ["lesson", "question"]:
            return "educational_content"
        elif update_type == "remediation":
            return "learning_gaps"
        else:
            return "educational_content"  # Default
    
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

# Global real-time updater instance
real_time_updater = RealTimeVectorUpdater()

# Webhook handlers for different content types
async def handle_lesson_update(lesson_id: str, operation: str, lesson_data: Dict[str, Any]):
    """Handle lesson script updates."""
    await real_time_updater.queue_update("lesson", lesson_id, operation, lesson_data)

async def handle_question_update(question_id: str, operation: str, question_data: Dict[str, Any]):
    """Handle question bank updates."""
    await real_time_updater.queue_update("question", question_id, operation, question_data)

async def handle_remediation_update(remediation_id: str, operation: str, remediation_data: Dict[str, Any]):
    """Handle remediation data updates."""
    await real_time_updater.queue_update("remediation", remediation_id, operation, remediation_data)

# Batch processing functions
async def process_bulk_updates(updates: List[Dict[str, Any]]):
    """Process a bulk of updates at once."""
    logger.info(f"📦 Processing {len(updates)} bulk updates")
    
    for update in updates:
        await real_time_updater.queue_update(
            update["update_type"],
            update["document_id"],
            update["operation"],
            update["data"]
        )

# Convenience functions for easy access
async def start_real_time_updates():
    """Start the real-time vector update system."""
    await real_time_updater.start_processing()

async def stop_real_time_updates():
    """Stop the real-time vector update system."""
    await real_time_updater.stop_processing()
