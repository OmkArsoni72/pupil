"""
Enhanced RAG Integration for Remedy Agent
Replaces the current LLM-only approach with vector search capabilities while maintaining backward compatibility.
"""

import os
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from services.db_operations.base import prerequisite_cache_collection
from services.ai.pinecone_client import (
    pinecone_client, 
    generate_embedding, 
    query_vectors,
    is_pinecone_available
)
import anyio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LLM for fallback operations
RAG_LLM = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.1,
    google_api_key=os.environ["GEMINI_API_KEY"],
)

class PrerequisiteTopic(BaseModel):
    topic: str
    grade_level: str
    priority: int
    description: Optional[str] = None
    learning_objectives: Optional[List[str]] = None
    success_rate: Optional[float] = None
    source: str = "vector_search"  # "vector_search", "llm_fallback", "cached"

class EnhancedRAGIntegration:
    """
    Enhanced RAG integration that combines vector search with LLM fallback.
    Maintains backward compatibility with existing rag_integration.py
    """
    
    def __init__(self):
        self.pinecone_available = is_pinecone_available()
        logger.info(f"Enhanced RAG Integration initialized. Pinecone available: {self.pinecone_available}")
    
    async def discover_prerequisites(
        self, 
        gap_code: str, 
        grade_level: str, 
        subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Enhanced prerequisite discovery using vector search with LLM fallback.
        
        Args:
            gap_code: The learning gap code
            grade_level: Current grade level
            subject: Subject area (optional)
        
        Returns:
            List of prerequisite topics with metadata
        """
        logger.info(f"🔍 [ENHANCED_RAG] Discovering prerequisites for gap: {gap_code}")
        
        # 1. Check cache first (existing logic)
        try:
            def _find_cache():
                return prerequisite_cache_collection.find_one({
                    "gap_code": gap_code, 
                    "grade_level": grade_level, 
                    "subject": subject
                })
            cached = await anyio.to_thread.run_sync(_find_cache)
            if cached and isinstance(cached.get("prerequisites"), list) and cached.get("prerequisites"):
                logger.info(f"🔍 [ENHANCED_RAG] Using cached prerequisites for {gap_code}")
                return cached["prerequisites"]
        except Exception as e:
            logger.warning(f"⚠️ [ENHANCED_RAG] Cache lookup failed: {e}")
        
        # 2. Try vector search if Pinecone is available
        if self.pinecone_available:
            try:
                prerequisites = await self._discover_with_vector_search(gap_code, grade_level, subject)
                if prerequisites:
                    logger.info(f"🔍 [ENHANCED_RAG] Found {len(prerequisites)} prerequisites via vector search")
                    # Cache the results
                    await self._cache_prerequisites(gap_code, grade_level, subject, prerequisites)
                    return prerequisites
            except Exception as e:
                logger.warning(f"⚠️ [ENHANCED_RAG] Vector search failed: {e}")
        
        # 3. Fallback to LLM approach (existing logic)
        logger.info(f"🔍 [ENHANCED_RAG] Falling back to LLM approach for {gap_code}")
        prerequisites = await self._discover_with_llm(gap_code, grade_level, subject)
        
        # Cache the fallback results
        await self._cache_prerequisites(gap_code, grade_level, subject, prerequisites)
        return prerequisites
    
    async def _discover_with_vector_search(
        self, 
        gap_code: str, 
        grade_level: str, 
        subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover prerequisites using vector search in Pinecone.
        """
        try:
            # Generate embedding for the gap
            query_text = f"{gap_code} {grade_level} {subject or ''}"
            query_embedding = await generate_embedding(query_text)
            
            # Search for similar gaps in learning_gaps index
            filter_dict = {}
            if grade_level:
                # Search for gaps at same or lower grade levels
                filter_dict["grade_level"] = {"$lte": grade_level}
            if subject:
                filter_dict["subject"] = subject
            
            similar_gaps = await query_vectors(
                index_name="learning_gaps",
                query_vector=query_embedding,
                top_k=10,
                filter_dict=filter_dict,
                include_metadata=True
            )
            
            if not similar_gaps:
                logger.info("No similar gaps found in vector database")
                return []
            
            # Extract prerequisite patterns from similar gaps
            prerequisites = self._extract_prerequisites_from_similar_gaps(similar_gaps, gap_code)
            
            # Also search educational content for related topics
            content_results = await query_vectors(
                index_name="educational_content",
                query_vector=query_embedding,
                top_k=5,
                filter_dict=filter_dict,
                include_metadata=True
            )
            
            # Extract additional prerequisites from content
            content_prerequisites = self._extract_prerequisites_from_content(content_results, gap_code)
            
            # Combine and deduplicate prerequisites
            all_prerequisites = prerequisites + content_prerequisites
            unique_prerequisites = self._deduplicate_prerequisites(all_prerequisites)
            
            return unique_prerequisites
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def _extract_prerequisites_from_similar_gaps(
        self, 
        similar_gaps: List[Dict[str, Any]], 
        gap_code: str
    ) -> List[Dict[str, Any]]:
        """
        Extract prerequisite patterns from similar learning gaps.
        """
        prerequisites = []
        
        for gap in similar_gaps:
            metadata = gap.get("metadata", {})
            success_rate = gap.get("score", 0.0)
            
            # Extract successful prerequisites from metadata
            successful_prerequisites = metadata.get("successful_prerequisites", [])
            learning_modes_used = metadata.get("learning_modes_used", [])
            
            for i, prereq in enumerate(successful_prerequisites):
                if isinstance(prereq, str):
                    prerequisites.append({
                        "topic": prereq,
                        "grade_level": metadata.get("grade_level", "unknown"),
                        "priority": i + 1,
                        "description": f"Prerequisite for {gap_code} based on similar gap success",
                        "learning_objectives": [],
                        "success_rate": success_rate,
                        "source": "vector_search",
                        "learning_modes": learning_modes_used
                    })
        
        return prerequisites
    
    def _extract_prerequisites_from_content(
        self, 
        content_results: List[Dict[str, Any]], 
        gap_code: str
    ) -> List[Dict[str, Any]]:
        """
        Extract prerequisites from educational content.
        """
        prerequisites = []
        
        for content in content_results:
            metadata = content.get("metadata", {})
            prerequisites_list = metadata.get("prerequisites", [])
            
            for i, prereq in enumerate(prerequisites_list):
                if isinstance(prereq, str):
                    prerequisites.append({
                        "topic": prereq,
                        "grade_level": metadata.get("grade_level", "unknown"),
                        "priority": i + 1,
                        "description": f"Prerequisite from educational content for {gap_code}",
                        "learning_objectives": metadata.get("learning_objectives", []),
                        "success_rate": content.get("score", 0.0),
                        "source": "vector_search",
                        "content_type": metadata.get("content_type", "unknown")
                    })
        
        return prerequisites
    
    def _deduplicate_prerequisites(self, prerequisites: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate prerequisites and merge information.
        """
        unique_prereqs = {}
        
        for prereq in prerequisites:
            topic = prereq.get("topic", "").lower()
            if topic in unique_prereqs:
                # Merge information, keeping the highest success rate
                existing = unique_prereqs[topic]
                if prereq.get("success_rate", 0) > existing.get("success_rate", 0):
                    unique_prereqs[topic] = prereq
            else:
                unique_prereqs[topic] = prereq
        
        # Sort by priority and success rate
        result = list(unique_prereqs.values())
        result.sort(key=lambda x: (x.get("priority", 999), -x.get("success_rate", 0)))
        
        return result
    
    async def _discover_with_llm(
        self, 
        gap_code: str, 
        grade_level: str, 
        subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fallback to LLM-based prerequisite discovery (existing logic).
        """
        # Build RAG query (existing logic from rag_integration.py)
        query = f"""
        For a student in grade {grade_level} struggling with: {gap_code}
        
        What are the prerequisite topics and concepts they need to master first?
        Provide a structured list of prerequisite topics in order of priority.
        
        For each prerequisite, include:
        - Topic name
        - Grade level where it's typically taught
        - Priority (1=most important, higher numbers=less critical)
        - Brief description
        - Key learning objectives
        
        Focus on foundational concepts that build up to understanding {gap_code}.
        """
        
        if subject:
            query += f"\nSubject area: {subject}"
        
        try:
            # Query LLM (existing logic)
            response = await RAG_LLM.ainvoke(query)
            
            # Parse response into structured prerequisites (existing logic)
            prerequisites = self._parse_rag_response(response.content, gap_code)
            
            # Add source information
            for prereq in prerequisites:
                prereq["source"] = "llm_fallback"
                prereq["success_rate"] = 0.5  # Default for LLM-generated
            
            logger.info(f"🔍 [ENHANCED_RAG] Found {len(prerequisites)} prerequisites via LLM")
            return prerequisites
            
        except Exception as e:
            logger.error(f"❌ [ENHANCED_RAG] Error in LLM prerequisite discovery: {str(e)}")
            # Return fallback prerequisites (existing logic)
            fallback = self._get_fallback_prerequisites(gap_code, grade_level)
            for prereq in fallback:
                prereq["source"] = "fallback"
                prereq["success_rate"] = 0.3  # Lower confidence for fallback
            return fallback
    
    def _parse_rag_response(self, response_text: str, gap_code: str) -> List[Dict[str, Any]]:
        """
        Parse LLM response into structured prerequisite data (existing logic).
        """
        prerequisites = []
        
        # Simple parsing logic - in production, this would be more sophisticated
        lines = response_text.split('\n')
        current_topic = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for topic indicators
            if line.startswith('-') or line.startswith('*') or line.startswith('1.') or line.startswith('2.'):
                # Extract topic name
                topic_name = line.lstrip('-*123456789. ').split(':')[0].strip()
                if topic_name:
                    current_topic = {
                        "topic": topic_name,
                        "grade_level": "previous",
                        "priority": len(prerequisites) + 1,
                        "description": "",
                        "learning_objectives": []
                    }
                    prerequisites.append(current_topic)
            elif current_topic and ('grade' in line.lower() or 'level' in line.lower()):
                # Extract grade level
                if 'grade' in line.lower():
                    try:
                        grade_part = line.lower().split('grade')[1].split()[0]
                        if grade_part.isdigit():
                            current_topic["grade_level"] = f"grade_{grade_part}"
                    except:
                        pass
            elif current_topic and line:
                # Add to description
                if not current_topic["description"]:
                    current_topic["description"] = line
                else:
                    current_topic["description"] += " " + line
        
        # If no structured prerequisites found, create generic ones
        if not prerequisites:
            prerequisites = self._get_fallback_prerequisites(gap_code, "unknown")
        
        return prerequisites
    
    def _get_fallback_prerequisites(self, gap_code: str, grade_level: str) -> List[Dict[str, Any]]:
        """
        Provide fallback prerequisites when all else fails (existing logic).
        """
        # Basic prerequisite mapping based on common patterns
        fallback_map = {
            "algebra": [
                {"topic": "basic_arithmetic", "grade_level": "elementary", "priority": 1, "description": "Basic addition, subtraction, multiplication, division"},
                {"topic": "number_sense", "grade_level": "elementary", "priority": 2, "description": "Understanding numbers and their relationships"},
                {"topic": "fractions", "grade_level": "elementary", "priority": 3, "description": "Understanding fractions and decimals"}
            ],
            "geometry": [
                {"topic": "basic_shapes", "grade_level": "elementary", "priority": 1, "description": "Recognition and properties of basic shapes"},
                {"topic": "measurement", "grade_level": "elementary", "priority": 2, "description": "Length, area, and perimeter concepts"},
                {"topic": "spatial_reasoning", "grade_level": "elementary", "priority": 3, "description": "Understanding spatial relationships"}
            ],
            "reading": [
                {"topic": "phonics", "grade_level": "kindergarten", "priority": 1, "description": "Letter-sound relationships"},
                {"topic": "vocabulary", "grade_level": "elementary", "priority": 2, "description": "Basic word recognition and meaning"},
                {"topic": "comprehension", "grade_level": "elementary", "priority": 3, "description": "Understanding what is read"}
            ]
        }
        
        # Find matching fallback
        gap_lower = gap_code.lower()
        for key, prereqs in fallback_map.items():
            if key in gap_lower:
                return prereqs
        
        # Generic fallback
        return [
            {
                "topic": "basic_concepts",
                "grade_level": "previous",
                "priority": 1,
                "description": f"Fundamental concepts needed for {gap_code}",
                "learning_objectives": [f"Understand basic principles of {gap_code}"]
            }
        ]
    
    async def _cache_prerequisites(
        self, 
        gap_code: str, 
        grade_level: str, 
        subject: Optional[str], 
        prerequisites: List[Dict[str, Any]]
    ) -> None:
        """
        Cache prerequisites in MongoDB (existing logic).
        """
        try:
            def _upsert():
                return prerequisite_cache_collection.update_one(
                    {"gap_code": gap_code, "grade_level": grade_level, "subject": subject},
                    {"$set": {
                        "gap_code": gap_code, 
                        "grade_level": grade_level, 
                        "subject": subject, 
                        "prerequisites": prerequisites
                    }},
                    upsert=True,
                )
            await anyio.to_thread.run_sync(_upsert)
        except Exception as e:
            logger.warning(f"⚠️ [ENHANCED_RAG] Failed to cache prerequisites: {e}")
    
    async def get_prerequisite_learning_path(self, prerequisites: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a learning path for prerequisite topics (existing logic).
        """
        logger.info(f"🗺️ [ENHANCED_RAG] Generating learning path for {len(prerequisites)} prerequisites")
        
        # Sort by priority
        sorted_prereqs = sorted(prerequisites, key=lambda x: x.get("priority", 999))
        
        learning_path = {
            "total_prerequisites": len(sorted_prereqs),
            "estimated_duration_hours": len(sorted_prereqs) * 2,  # 2 hours per prerequisite
            "prerequisite_sequence": sorted_prereqs,
            "learning_strategy": "sequential_mastery",
            "assessment_checkpoints": []
        }
        
        # Add assessment checkpoints
        for i, prereq in enumerate(sorted_prereqs):
            learning_path["assessment_checkpoints"].append({
                "prerequisite_index": i,
                "topic": prereq["topic"],
                "assessment_type": "mastery_check",
                "passing_threshold": 0.8
            })
        
        return learning_path

# Global instance for backward compatibility
enhanced_rag = EnhancedRAGIntegration()

# Backward compatibility functions
async def discover_prerequisites(gap_code: str, grade_level: str, subject: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Backward compatible function that uses enhanced RAG integration.
    """
    return await enhanced_rag.discover_prerequisites(gap_code, grade_level, subject)

async def get_prerequisite_learning_path(prerequisites: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Backward compatible function for learning path generation.
    """
    return await enhanced_rag.get_prerequisite_learning_path(prerequisites)

