"""
Content Recommendation Engine for RAG System
Provides blazing fast content recommendations based on vector similarity search.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import anyio

from services.ai.pinecone_client import query_vectors, generate_embedding
from services.ai.vector_schemas import (
    create_combined_filter, create_grade_level_filter, create_subject_filter,
    create_difficulty_filter, create_success_rate_filter
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContentRecommendationEngine:
    """
    High-performance content recommendation engine using vector similarity search.
    Optimized for blazing fast recommendations based on learning gaps and student profiles.
    """
    
    def __init__(self):
        self.recommendation_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def recommend_content_for_gap(
        self,
        gap_code: str,
        gap_type: str,
        grade_level: str,
        subject: str,
        student_profile: Optional[Dict[str, Any]] = None,
        max_recommendations: int = 10
    ) -> Dict[str, Any]:
        """
        Recommend educational content for a specific learning gap.
        """
        logger.info(f"🎯 Recommending content for gap: {gap_code} ({gap_type})")
        
        # Create search query
        search_query = f"{gap_code} {gap_type} {grade_level} {subject}"
        
        # Generate embedding for search
        query_embedding = await generate_embedding(search_query)
        
        # Create filters
        filters = create_combined_filter(
            grade_level=grade_level,
            subject=subject,
            include_lower_grades=True
        )
        
        # Search educational content
        content_results = await query_vectors(
            "educational_content",
            query_embedding,
            top_k=max_recommendations * 2,  # Get more results for filtering
            filter_dict=filters,
            include_metadata=True
        )
        
        # Search learning gaps for similar successful cases
        gap_results = await query_vectors(
            "learning_gaps",
            query_embedding,
            top_k=5,
            filter_dict=filters,
            include_metadata=True
        )
        
        # Process and rank recommendations
        recommendations = await self._process_recommendations(
            content_results, gap_results, student_profile, max_recommendations
        )
        
        return {
            "gap_code": gap_code,
            "gap_type": gap_type,
            "recommendations": recommendations,
            "total_found": len(content_results) + len(gap_results),
            "recommendation_metadata": {
                "search_query": search_query,
                "filters_applied": filters,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def recommend_similar_students(
        self,
        student_id: str,
        learning_gaps: List[Dict[str, Any]],
        max_recommendations: int = 5
    ) -> Dict[str, Any]:
        """
        Find students with similar learning patterns for collaborative learning.
        """
        logger.info(f"👥 Finding similar students for student: {student_id}")
        
        # Create student profile embedding
        profile_text = self._create_student_profile_text(learning_gaps)
        profile_embedding = await generate_embedding(profile_text)
        
        # Search for similar learning patterns
        similar_gaps = await query_vectors(
            "learning_gaps",
            profile_embedding,
            top_k=max_recommendations * 3,
            include_metadata=True
        )
        
        # Group by student and analyze patterns
        student_patterns = {}
        for gap_result in similar_gaps:
            metadata = gap_result.get("metadata", {})
            student_id_found = metadata.get("student_id")
            
            if student_id_found and student_id_found != student_id:
                if student_id_found not in student_patterns:
                    student_patterns[student_id_found] = {
                        "student_id": student_id_found,
                        "similar_gaps": [],
                        "success_rate": 0.0,
                        "similarity_score": 0.0
                    }
                
                student_patterns[student_id_found]["similar_gaps"].append({
                    "gap_code": metadata.get("gap_code"),
                    "gap_type": metadata.get("gap_type"),
                    "similarity_score": gap_result.get("score", 0.0)
                })
        
        # Calculate similarity scores and success rates
        similar_students = []
        for student_id_found, pattern in student_patterns.items():
            if len(pattern["similar_gaps"]) >= 2:  # At least 2 similar gaps
                avg_similarity = sum(
                    gap["similarity_score"] for gap in pattern["similar_gaps"]
                ) / len(pattern["similar_gaps"])
                
                pattern["similarity_score"] = avg_similarity
                pattern["success_rate"] = metadata.get("remediation_success_rate", 0.0)
                similar_students.append(pattern)
        
        # Sort by similarity and success rate
        similar_students.sort(
            key=lambda x: (x["similarity_score"], x["success_rate"]),
            reverse=True
        )
        
        return {
            "student_id": student_id,
            "similar_students": similar_students[:max_recommendations],
            "total_analyzed": len(student_patterns),
            "recommendation_metadata": {
                "profile_text": profile_text,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def recommend_learning_modes(
        self,
        gap_type: str,
        grade_level: str,
        subject: str,
        student_preferences: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Recommend optimal learning modes based on gap type and historical success.
        """
        logger.info(f"🎮 Recommending learning modes for {gap_type} gaps")
        
        # Create search query for learning mode effectiveness
        search_query = f"{gap_type} learning modes effectiveness {grade_level} {subject}"
        query_embedding = await generate_embedding(search_query)
        
        # Search learning gaps for successful remediation patterns
        gap_results = await query_vectors(
            "learning_gaps",
            query_embedding,
            top_k=20,
            filter_dict=create_combined_filter(
                grade_level=grade_level,
                subject=subject
            ),
            include_metadata=True
        )
        
        # Analyze learning mode effectiveness
        mode_effectiveness = {}
        for gap_result in gap_results:
            metadata = gap_result.get("metadata", {})
            success_rate = metadata.get("remediation_success_rate", 0.0)
            learning_modes = metadata.get("learning_modes_used", [])
            
            for mode in learning_modes:
                if mode not in mode_effectiveness:
                    mode_effectiveness[mode] = {
                        "mode": mode,
                        "total_uses": 0,
                        "total_success_rate": 0.0,
                        "success_count": 0
                    }
                
                mode_effectiveness[mode]["total_uses"] += 1
                mode_effectiveness[mode]["total_success_rate"] += success_rate
                if success_rate > 0.7:  # Consider >70% as successful
                    mode_effectiveness[mode]["success_count"] += 1
        
        # Calculate effectiveness scores
        recommended_modes = []
        for mode, stats in mode_effectiveness.items():
            if stats["total_uses"] >= 2:  # At least 2 uses for reliability
                avg_success_rate = stats["total_success_rate"] / stats["total_uses"]
                effectiveness_score = (
                    avg_success_rate * 0.7 +  # 70% weight on success rate
                    (stats["success_count"] / stats["total_uses"]) * 0.3  # 30% weight on success count
                )
                
                recommended_modes.append({
                    "mode": mode,
                    "effectiveness_score": effectiveness_score,
                    "avg_success_rate": avg_success_rate,
                    "total_uses": stats["total_uses"],
                    "success_count": stats["success_count"]
                })
        
        # Sort by effectiveness
        recommended_modes.sort(key=lambda x: x["effectiveness_score"], reverse=True)
        
        # Apply student preferences if provided
        if student_preferences:
            preferred_modes = student_preferences.get("preferred_modes", [])
            for mode in recommended_modes:
                if mode["mode"] in preferred_modes:
                    mode["effectiveness_score"] *= 1.2  # Boost preferred modes
        
        return {
            "gap_type": gap_type,
            "recommended_modes": recommended_modes[:8],  # Top 8 modes
            "total_analyzed": len(gap_results),
            "recommendation_metadata": {
                "search_query": search_query,
                "student_preferences_applied": bool(student_preferences),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def recommend_questions(
        self,
        topic: str,
        grade_level: str,
        subject: str,
        difficulty: str = "medium",
        question_type: Optional[str] = None,
        max_recommendations: int = 10
    ) -> Dict[str, Any]:
        """
        Recommend questions based on topic and difficulty.
        """
        logger.info(f"❓ Recommending questions for topic: {topic}")
        
        # Create search query
        search_query = f"{topic} {difficulty} questions {grade_level} {subject}"
        query_embedding = await generate_embedding(search_query)
        
        # Create filters
        filters = create_combined_filter(
            grade_level=grade_level,
            subject=subject,
            difficulty=difficulty
        )
        
        # Search questions
        question_results = await query_vectors(
            "educational_content",
            query_embedding,
            top_k=max_recommendations * 2,
            filter_dict=filters,
            include_metadata=True
        )
        
        # Filter by question type if specified
        if question_type:
            question_results = [
                q for q in question_results
                if q.get("metadata", {}).get("content_type") == "question" and
                q.get("metadata", {}).get("question_type") == question_type
            ]
        
        # Process and rank questions
        recommended_questions = []
        for result in question_results[:max_recommendations]:
            metadata = result.get("metadata", {})
            if metadata.get("content_type") == "question":
                recommended_questions.append({
                    "question_id": result.get("id"),
                    "question_text": metadata.get("question_text", ""),
                    "question_type": metadata.get("question_type", ""),
                    "difficulty": metadata.get("difficulty", ""),
                    "topics": metadata.get("topics", []),
                    "learning_outcomes": metadata.get("learning_outcomes", []),
                    "similarity_score": result.get("score", 0.0),
                    "statistics": metadata.get("statistics", {})
                })
        
        return {
            "topic": topic,
            "difficulty": difficulty,
            "recommended_questions": recommended_questions,
            "total_found": len(question_results),
            "recommendation_metadata": {
                "search_query": search_query,
                "filters_applied": filters,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _create_student_profile_text(self, learning_gaps: List[Dict[str, Any]]) -> str:
        """Create text representation of student learning profile."""
        gap_codes = [gap.get("code", "") for gap in learning_gaps]
        gap_types = [gap.get("type", "") for gap in learning_gaps]
        
        return f"Student learning gaps: {', '.join(gap_codes)}. Gap types: {', '.join(gap_types)}"
    
    async def _process_recommendations(
        self,
        content_results: List[Dict[str, Any]],
        gap_results: List[Dict[str, Any]],
        student_profile: Optional[Dict[str, Any]],
        max_recommendations: int
    ) -> List[Dict[str, Any]]:
        """Process and rank content recommendations."""
        recommendations = []
        
        # Process content recommendations
        for result in content_results:
            metadata = result.get("metadata", {})
            recommendation = {
                "content_id": result.get("id"),
                "content_type": metadata.get("content_type", ""),
                "topic": metadata.get("topic", ""),
                "subject": metadata.get("subject", ""),
                "grade_level": metadata.get("grade_level", ""),
                "difficulty": metadata.get("difficulty", ""),
                "similarity_score": result.get("score", 0.0),
                "success_rate": metadata.get("success_rate", 0.0),
                "usage_count": metadata.get("usage_count", 0),
                "learning_objectives": metadata.get("learning_objectives", []),
                "prerequisites": metadata.get("prerequisites", [])
            }
            recommendations.append(recommendation)
        
        # Process gap-based recommendations
        for result in gap_results:
            metadata = result.get("metadata", {})
            successful_prerequisites = metadata.get("successful_prerequisites", [])
            learning_modes = metadata.get("learning_modes_used", [])
            
            if successful_prerequisites or learning_modes:
                recommendation = {
                    "content_id": f"gap_based_{result.get('id')}",
                    "content_type": "remediation_pattern",
                    "topic": metadata.get("gap_code", ""),
                    "subject": metadata.get("subject", ""),
                    "grade_level": metadata.get("grade_level", ""),
                    "similarity_score": result.get("score", 0.0),
                    "success_rate": metadata.get("remediation_success_rate", 0.0),
                    "successful_prerequisites": successful_prerequisites,
                    "effective_learning_modes": learning_modes,
                    "time_to_resolve": metadata.get("time_to_resolve_hours", 0.0)
                }
                recommendations.append(recommendation)
        
        # Rank recommendations
        recommendations.sort(
            key=lambda x: (
                x["similarity_score"] * 0.4 +  # 40% weight on similarity
                x["success_rate"] * 0.3 +      # 30% weight on success rate
                min(x.get("usage_count", 0) / 100, 1.0) * 0.3  # 30% weight on usage
            ),
            reverse=True
        )
        
        # Apply student profile preferences if available
        if student_profile:
            preferred_difficulties = student_profile.get("preferred_difficulties", [])
            preferred_subjects = student_profile.get("preferred_subjects", [])
            
            for rec in recommendations:
                if rec.get("difficulty") in preferred_difficulties:
                    rec["similarity_score"] *= 1.1
                if rec.get("subject") in preferred_subjects:
                    rec["similarity_score"] *= 1.1
        
        return recommendations[:max_recommendations]

# Global recommendation engine instance
recommendation_engine = ContentRecommendationEngine()

# Convenience functions for easy access
async def recommend_content_for_gap(
    gap_code: str,
    gap_type: str,
    grade_level: str,
    subject: str,
    student_profile: Optional[Dict[str, Any]] = None,
    max_recommendations: int = 10
) -> Dict[str, Any]:
    """Recommend content for a learning gap."""
    return await recommendation_engine.recommend_content_for_gap(
        gap_code, gap_type, grade_level, subject, student_profile, max_recommendations
    )

async def recommend_similar_students(
    student_id: str,
    learning_gaps: List[Dict[str, Any]],
    max_recommendations: int = 5
) -> Dict[str, Any]:
    """Find students with similar learning patterns."""
    return await recommendation_engine.recommend_similar_students(
        student_id, learning_gaps, max_recommendations
    )

async def recommend_learning_modes(
    gap_type: str,
    grade_level: str,
    subject: str,
    student_preferences: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Recommend optimal learning modes."""
    return await recommendation_engine.recommend_learning_modes(
        gap_type, grade_level, subject, student_preferences
    )

async def recommend_questions(
    topic: str,
    grade_level: str,
    subject: str,
    difficulty: str = "medium",
    question_type: Optional[str] = None,
    max_recommendations: int = 10
) -> Dict[str, Any]:
    """Recommend questions for a topic."""
    return await recommendation_engine.recommend_questions(
        topic, grade_level, subject, difficulty, question_type, max_recommendations
    )
