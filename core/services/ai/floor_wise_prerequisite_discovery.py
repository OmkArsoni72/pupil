"""
Floor-wise Prerequisite Discovery for Foundational Gap Remediation
Implements PRD-compliant prerequisite discovery with proper grade-level hierarchy.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import anyio

from services.ai.pinecone_client import query_vectors, generate_embedding, is_pinecone_available
from services.ai.vector_schemas import create_combined_filter
from services.db_operations.base import prerequisite_cache_collection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FloorWisePrerequisiteDiscovery:
    """
    Implements floor-wise prerequisite discovery for foundational gaps.
    Returns structured "floor-wise grade plan" showing topic hierarchy.
    """
    
    def __init__(self):
        self.pinecone_available = is_pinecone_available()
        logger.info(f"Floor-wise Prerequisite Discovery initialized. Pinecone available: {self.pinecone_available}")
    
    async def discover_floor_wise_prerequisites(
        self,
        gap_code: str,
        current_grade: str,
        subject: Optional[str] = None,
        max_grade_levels: int = 3
    ) -> Dict[str, Any]:
        """
        Discover floor-wise prerequisites for foundational gaps.
        
        Args:
            gap_code: The learning gap code
            current_grade: Current grade level (e.g., "grade_10")
            subject: Subject area (optional)
            max_grade_levels: Maximum number of grade levels to go back
        
        Returns:
            Floor-wise grade plan with prerequisite hierarchy
        """
        logger.info(f"🏗️ [FLOOR_WISE] Discovering prerequisites for gap: {gap_code} at grade: {current_grade}")
        
        # 1. Check cache first
        cached_plan = await self._get_cached_floor_plan(gap_code, current_grade, subject)
        if cached_plan:
            logger.info(f"🏗️ [FLOOR_WISE] Using cached floor plan for {gap_code}")
            return cached_plan
        
        # 2. Try vector search if Pinecone is available
        if self.pinecone_available:
            try:
                floor_plan = await self._discover_with_vector_search(
                    gap_code, current_grade, subject, max_grade_levels
                )
                if floor_plan and floor_plan.get("prerequisite_floors"):
                    logger.info(f"🏗️ [FLOOR_WISE] Found floor plan via vector search")
                    await self._cache_floor_plan(gap_code, current_grade, subject, floor_plan)
                    return floor_plan
            except Exception as e:
                logger.warning(f"⚠️ [FLOOR_WISE] Vector search failed: {e}")
        
        # 3. Fallback to structured prerequisite mapping
        logger.info(f"🏗️ [FLOOR_WISE] Falling back to structured mapping for {gap_code}")
        floor_plan = await self._generate_structured_floor_plan(
            gap_code, current_grade, subject, max_grade_levels
        )
        
        # Cache the fallback results
        await self._cache_floor_plan(gap_code, current_grade, subject, floor_plan)
        return floor_plan
    
    async def _discover_with_vector_search(
        self,
        gap_code: str,
        current_grade: str,
        subject: Optional[str],
        max_grade_levels: int
    ) -> Dict[str, Any]:
        """
        Discover prerequisites using vector search in Pinecone.
        """
        try:
            # Generate embedding for the gap
            query_text = f"{gap_code} {current_grade} {subject or ''} prerequisites"
            query_embedding = await generate_embedding(query_text)
            
            # Search for similar gaps and their successful prerequisites
            filter_dict = {}
            if subject:
                filter_dict["subject"] = subject
            
            # Search learning gaps for successful remediation patterns
            similar_gaps = await query_vectors(
                index_name="learning_gaps",
                query_vector=query_embedding,
                top_k=10,
                filter_dict=filter_dict,
                include_metadata=True
            )
            
            # Search educational content for prerequisite relationships
            content_results = await query_vectors(
                index_name="educational_content",
                query_vector=query_embedding,
                top_k=15,
                filter_dict=filter_dict,
                include_metadata=True
            )
            
            # Build floor-wise plan from search results
            floor_plan = self._build_floor_plan_from_results(
                similar_gaps, content_results, gap_code, current_grade, max_grade_levels
            )
            
            return floor_plan
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return {}
    
    def _build_floor_plan_from_results(
        self,
        similar_gaps: List[Dict[str, Any]],
        content_results: List[Dict[str, Any]],
        gap_code: str,
        current_grade: str,
        max_grade_levels: int
    ) -> Dict[str, Any]:
        """
        Build floor-wise plan from vector search results.
        """
        prerequisite_floors = []
        grade_levels = self._get_grade_levels(current_grade, max_grade_levels)
        
        for grade_level in grade_levels:
            floor_topics = []
            
            # Extract prerequisites from similar gaps
            for gap in similar_gaps:
                metadata = gap.get("metadata", {})
                if metadata.get("grade_level") == grade_level:
                    successful_prereqs = metadata.get("successful_prerequisites", [])
                    for prereq in successful_prereqs:
                        if isinstance(prereq, str):
                            floor_topics.append({
                                "topic": prereq,
                                "priority": len(floor_topics) + 1,
                                "source": "similar_gap_success",
                                "success_rate": gap.get("score", 0.0)
                            })
            
            # Extract prerequisites from educational content
            for content in content_results:
                metadata = content.get("metadata", {})
                if metadata.get("grade_level") == grade_level:
                    prerequisites = metadata.get("prerequisites", [])
                    for prereq in prerequisites:
                        if isinstance(prereq, str):
                            floor_topics.append({
                                "topic": prereq,
                                "priority": len(floor_topics) + 1,
                                "source": "educational_content",
                                "success_rate": content.get("score", 0.0)
                            })
            
            # Deduplicate and sort by priority
            unique_topics = self._deduplicate_topics(floor_topics)
            if unique_topics:
                prerequisite_floors.append({
                    "grade_level": grade_level,
                    "topics": unique_topics,
                    "estimated_duration_hours": len(unique_topics) * 2,
                    "mastery_threshold": 0.8
                })
        
        return {
            "gap_code": gap_code,
            "current_grade": current_grade,
            "subject": subject,
            "prerequisite_floors": prerequisite_floors,
            "total_estimated_hours": sum(floor["estimated_duration_hours"] for floor in prerequisite_floors),
            "discovery_method": "vector_search",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _generate_structured_floor_plan(
        self,
        gap_code: str,
        current_grade: str,
        subject: Optional[str],
        max_grade_levels: int
    ) -> Dict[str, Any]:
        """
        Generate structured floor plan using predefined prerequisite mappings.
        """
        grade_levels = self._get_grade_levels(current_grade, max_grade_levels)
        prerequisite_floors = []
        
        # Get structured prerequisites for each grade level
        for grade_level in grade_levels:
            topics = self._get_structured_prerequisites(gap_code, grade_level, subject)
            if topics:
                prerequisite_floors.append({
                    "grade_level": grade_level,
                    "topics": topics,
                    "estimated_duration_hours": len(topics) * 2,
                    "mastery_threshold": 0.8
                })
        
        return {
            "gap_code": gap_code,
            "current_grade": current_grade,
            "subject": subject,
            "prerequisite_floors": prerequisite_floors,
            "total_estimated_hours": sum(floor["estimated_duration_hours"] for floor in prerequisite_floors),
            "discovery_method": "structured_mapping",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_grade_levels(self, current_grade: str, max_levels: int) -> List[str]:
        """
        Get list of grade levels going backwards from current grade.
        """
        grade_mapping = {
            "grade_12": 12, "grade_11": 11, "grade_10": 10, "grade_9": 9,
            "grade_8": 8, "grade_7": 7, "grade_6": 6, "grade_5": 5,
            "grade_4": 4, "grade_3": 3, "grade_2": 2, "grade_1": 1
        }
        
        current_level = grade_mapping.get(current_grade, 10)
        grade_levels = []
        
        for i in range(max_levels):
            level = current_level - i - 1
            if level >= 1:
                grade_levels.append(f"grade_{level}")
        
        return grade_levels
    
    def _get_structured_prerequisites(
        self,
        gap_code: str,
        grade_level: str,
        subject: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Get structured prerequisites based on gap code and grade level.
        """
        # Comprehensive prerequisite mapping by subject and gap type
        prerequisite_mappings = {
            "mathematics": {
                "algebra": {
                    "grade_9": [
                        {"topic": "linear_equations", "priority": 1, "description": "Solving linear equations"},
                        {"topic": "graphing", "priority": 2, "description": "Graphing linear functions"},
                        {"topic": "inequalities", "priority": 3, "description": "Solving inequalities"}
                    ],
                    "grade_8": [
                        {"topic": "fractions", "priority": 1, "description": "Operations with fractions"},
                        {"topic": "decimals", "priority": 2, "description": "Decimal operations"},
                        {"topic": "percentages", "priority": 3, "description": "Percentage calculations"}
                    ],
                    "grade_7": [
                        {"topic": "basic_arithmetic", "priority": 1, "description": "Addition, subtraction, multiplication, division"},
                        {"topic": "order_of_operations", "priority": 2, "description": "PEMDAS/BODMAS rules"},
                        {"topic": "number_properties", "priority": 3, "description": "Commutative, associative, distributive properties"}
                    ]
                },
                "geometry": {
                    "grade_9": [
                        {"topic": "coordinate_geometry", "priority": 1, "description": "Points, lines, and planes"},
                        {"topic": "transformations", "priority": 2, "description": "Reflections, rotations, translations"},
                        {"topic": "similarity", "priority": 3, "description": "Similar triangles and ratios"}
                    ],
                    "grade_8": [
                        {"topic": "angles", "priority": 1, "description": "Types of angles and angle relationships"},
                        {"topic": "triangles", "priority": 2, "description": "Triangle properties and types"},
                        {"topic": "quadrilaterals", "priority": 3, "description": "Properties of quadrilaterals"}
                    ],
                    "grade_7": [
                        {"topic": "basic_shapes", "priority": 1, "description": "Recognition of basic geometric shapes"},
                        {"topic": "perimeter", "priority": 2, "description": "Calculating perimeter"},
                        {"topic": "area", "priority": 3, "description": "Calculating area of basic shapes"}
                    ]
                }
            },
            "physics": {
                "mechanics": {
                    "grade_10": [
                        {"topic": "kinematics", "priority": 1, "description": "Motion in one dimension"},
                        {"topic": "dynamics", "priority": 2, "description": "Forces and Newton's laws"},
                        {"topic": "energy", "priority": 3, "description": "Work, energy, and power"}
                    ],
                    "grade_9": [
                        {"topic": "measurement", "priority": 1, "description": "Units and measurements"},
                        {"topic": "motion_basics", "priority": 2, "description": "Basic concepts of motion"},
                        {"topic": "force_basics", "priority": 3, "description": "Introduction to forces"}
                    ]
                }
            },
            "chemistry": {
                "atomic_structure": {
                    "grade_10": [
                        {"topic": "periodic_table", "priority": 1, "description": "Elements and periodic trends"},
                        {"topic": "chemical_bonding", "priority": 2, "description": "Ionic and covalent bonds"},
                        {"topic": "molecular_structure", "priority": 3, "description": "Molecular geometry"}
                    ],
                    "grade_9": [
                        {"topic": "atoms", "priority": 1, "description": "Basic atomic structure"},
                        {"topic": "elements", "priority": 2, "description": "Elements and compounds"},
                        {"topic": "chemical_reactions", "priority": 3, "description": "Types of chemical reactions"}
                    ]
                }
            }
        }
        
        # Find matching prerequisites
        gap_lower = gap_code.lower()
        topics = []
        
        # Try to match by subject and gap type
        if subject and subject.lower() in prerequisite_mappings:
            subject_map = prerequisite_mappings[subject.lower()]
            for gap_type, grade_map in subject_map.items():
                if gap_type in gap_lower and grade_level in grade_map:
                    topics = grade_map[grade_level]
                    break
        
        # If no specific match, try generic math prerequisites
        if not topics and "math" in gap_lower or "algebra" in gap_lower or "geometry" in gap_lower:
            math_map = prerequisite_mappings.get("mathematics", {})
            for gap_type, grade_map in math_map.items():
                if gap_type in gap_lower and grade_level in grade_map:
                    topics = grade_map[grade_level]
                    break
        
        # Add source information
        for topic in topics:
            topic["source"] = "structured_mapping"
            topic["success_rate"] = 0.7  # Default confidence for structured mapping
        
        return topics
    
    def _deduplicate_topics(self, topics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate topics and merge information.
        """
        unique_topics = {}
        
        for topic in topics:
            topic_name = topic.get("topic", "").lower()
            if topic_name in unique_topics:
                # Keep the topic with higher success rate
                existing = unique_topics[topic_name]
                if topic.get("success_rate", 0) > existing.get("success_rate", 0):
                    unique_topics[topic_name] = topic
            else:
                unique_topics[topic_name] = topic
        
        # Sort by priority
        result = list(unique_topics.values())
        result.sort(key=lambda x: x.get("priority", 999))
        
        return result
    
    async def _get_cached_floor_plan(
        self,
        gap_code: str,
        current_grade: str,
        subject: Optional[str]
    ) -> Optional[Dict[str, Any]]:
        """Get cached floor plan if available."""
        try:
            def _find_cache():
                return prerequisite_cache_collection.find_one({
                    "gap_code": gap_code,
                    "current_grade": current_grade,
                    "subject": subject,
                    "plan_type": "floor_wise"
                })
            cached = await anyio.to_thread.run_sync(_find_cache)
            if cached and cached.get("floor_plan"):
                return cached["floor_plan"]
        except Exception as e:
            logger.warning(f"Cache lookup failed: {e}")
        return None
    
    async def _cache_floor_plan(
        self,
        gap_code: str,
        current_grade: str,
        subject: Optional[str],
        floor_plan: Dict[str, Any]
    ) -> None:
        """Cache floor plan in MongoDB."""
        try:
            def _upsert():
                return prerequisite_cache_collection.update_one(
                    {
                        "gap_code": gap_code,
                        "current_grade": current_grade,
                        "subject": subject,
                        "plan_type": "floor_wise"
                    },
                    {"$set": {
                        "gap_code": gap_code,
                        "current_grade": current_grade,
                        "subject": subject,
                        "plan_type": "floor_wise",
                        "floor_plan": floor_plan,
                        "cached_at": datetime.utcnow().isoformat()
                    }},
                    upsert=True,
                )
            await anyio.to_thread.run_sync(_upsert)
        except Exception as e:
            logger.warning(f"Failed to cache floor plan: {e}")

# Global instance
floor_wise_discovery = FloorWisePrerequisiteDiscovery()

# Convenience function for backward compatibility
async def discover_floor_wise_prerequisites(
    gap_code: str,
    current_grade: str,
    subject: Optional[str] = None,
    max_grade_levels: int = 3
) -> Dict[str, Any]:
    """
    Discover floor-wise prerequisites for foundational gaps.
    """
    return await floor_wise_discovery.discover_floor_wise_prerequisites(
        gap_code, current_grade, subject, max_grade_levels
    )
