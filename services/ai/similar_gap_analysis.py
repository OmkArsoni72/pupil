"""
Similar Gap Analysis for RAG System
Analyzes learning patterns and finds students with similar gaps for collaborative learning.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import anyio

from services.ai.pinecone_client import query_vectors, generate_embedding
from services.ai.vector_schemas import create_combined_filter
from services.db_operations.base import student_reports_collection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimilarGapAnalyzer:
    """
    Analyzes learning patterns and finds students with similar gaps.
    Provides insights for collaborative learning and remediation strategies.
    """
    
    def __init__(self):
        self.analysis_cache = {}
        self.cache_ttl = 600  # 10 minutes
    
    async def find_similar_students(
        self,
        student_id: str,
        learning_gaps: List[Dict[str, Any]],
        max_recommendations: int = 5,
        min_similarity_threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Find students with similar learning patterns and gaps.
        """
        logger.info(f"🔍 Finding similar students for student: {student_id}")
        
        # Create student profile embedding
        profile_text = self._create_student_profile_text(learning_gaps)
        profile_embedding = await generate_embedding(profile_text)
        
        # Search for similar learning patterns in vector database
        similar_gaps = await query_vectors(
            "learning_gaps",
            profile_embedding,
            top_k=max_recommendations * 5,  # Get more results for filtering
            include_metadata=True
        )
        
        # Group by student and analyze patterns
        student_patterns = {}
        for gap_result in similar_gaps:
            metadata = gap_result.get("metadata", {})
            student_id_found = metadata.get("student_id")
            similarity_score = gap_result.get("score", 0.0)
            
            if (student_id_found and 
                student_id_found != student_id and 
                similarity_score >= min_similarity_threshold):
                
                if student_id_found not in student_patterns:
                    student_patterns[student_id_found] = {
                        "student_id": student_id_found,
                        "similar_gaps": [],
                        "success_rate": 0.0,
                        "similarity_score": 0.0,
                        "gap_types": set(),
                        "subjects": set(),
                        "grade_level": metadata.get("grade_level", "unknown")
                    }
                
                pattern = student_patterns[student_id_found]
                pattern["similar_gaps"].append({
                    "gap_code": metadata.get("gap_code", ""),
                    "gap_type": metadata.get("gap_type", ""),
                    "similarity_score": similarity_score,
                    "success_rate": metadata.get("remediation_success_rate", 0.0)
                })
                pattern["gap_types"].add(metadata.get("gap_type", ""))
                pattern["subjects"].add(metadata.get("subject", ""))
        
        # Calculate similarity scores and success rates
        similar_students = []
        for student_id_found, pattern in student_patterns.items():
            if len(pattern["similar_gaps"]) >= 2:  # At least 2 similar gaps
                avg_similarity = sum(
                    gap["similarity_score"] for gap in pattern["similar_gaps"]
                ) / len(pattern["similar_gaps"])
                
                avg_success_rate = sum(
                    gap["success_rate"] for gap in pattern["similar_gaps"]
                ) / len(pattern["similar_gaps"])
                
                pattern["similarity_score"] = avg_similarity
                pattern["success_rate"] = avg_success_rate
                pattern["gap_types"] = list(pattern["gap_types"])
                pattern["subjects"] = list(pattern["subjects"])
                
                # Calculate pattern strength
                pattern["pattern_strength"] = (
                    avg_similarity * 0.4 +  # 40% weight on similarity
                    avg_success_rate * 0.3 +  # 30% weight on success rate
                    min(len(pattern["similar_gaps"]) / 10, 1.0) * 0.3  # 30% weight on gap count
                )
                
                similar_students.append(pattern)
        
        # Sort by pattern strength
        similar_students.sort(key=lambda x: x["pattern_strength"], reverse=True)
        
        return {
            "student_id": student_id,
            "similar_students": similar_students[:max_recommendations],
            "total_analyzed": len(student_patterns),
            "analysis_metadata": {
                "profile_text": profile_text,
                "min_similarity_threshold": min_similarity_threshold,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def analyze_remediation_effectiveness(
        self,
        gap_type: str,
        grade_level: str,
        subject: Optional[str] = None,
        time_period_days: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze remediation effectiveness for specific gap types.
        """
        logger.info(f"📊 Analyzing remediation effectiveness for {gap_type} gaps")
        
        # Create search query
        search_query = f"{gap_type} remediation effectiveness {grade_level} {subject or ''}"
        query_embedding = await generate_embedding(search_query)
        
        # Create time filter
        time_filter = {}
        if time_period_days:
            cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
            time_filter["created_at"] = {"$gte": cutoff_date.isoformat()}
        
        # Search learning gaps
        gap_results = await query_vectors(
            "learning_gaps",
            query_embedding,
            top_k=50,
            filter_dict=create_combined_filter(
                grade_level=grade_level,
                subject=subject
            ),
            include_metadata=True
        )
        
        # Analyze remediation patterns
        remediation_stats = {
            "total_cases": len(gap_results),
            "successful_cases": 0,
            "failed_cases": 0,
            "average_resolution_time": 0.0,
            "learning_mode_effectiveness": {},
            "prerequisite_effectiveness": {},
            "success_patterns": [],
            "failure_patterns": []
        }
        
        resolution_times = []
        
        for gap_result in gap_results:
            metadata = gap_result.get("metadata", {})
            success_rate = metadata.get("remediation_success_rate", 0.0)
            resolution_time = metadata.get("time_to_resolve_hours", 0.0)
            learning_modes = metadata.get("learning_modes_used", [])
            prerequisites = metadata.get("successful_prerequisites", [])
            
            # Categorize success/failure
            if success_rate > 0.7:
                remediation_stats["successful_cases"] += 1
                remediation_stats["success_patterns"].append({
                    "gap_code": metadata.get("gap_code", ""),
                    "success_rate": success_rate,
                    "learning_modes": learning_modes,
                    "prerequisites": prerequisites,
                    "resolution_time": resolution_time
                })
            else:
                remediation_stats["failed_cases"] += 1
                remediation_stats["failure_patterns"].append({
                    "gap_code": metadata.get("gap_code", ""),
                    "success_rate": success_rate,
                    "learning_modes": learning_modes,
                    "prerequisites": prerequisites,
                    "resolution_time": resolution_time
                })
            
            if resolution_time > 0:
                resolution_times.append(resolution_time)
            
            # Analyze learning mode effectiveness
            for mode in learning_modes:
                if mode not in remediation_stats["learning_mode_effectiveness"]:
                    remediation_stats["learning_mode_effectiveness"][mode] = {
                        "total_uses": 0,
                        "total_success_rate": 0.0,
                        "success_count": 0
                    }
                
                stats = remediation_stats["learning_mode_effectiveness"][mode]
                stats["total_uses"] += 1
                stats["total_success_rate"] += success_rate
                if success_rate > 0.7:
                    stats["success_count"] += 1
            
            # Analyze prerequisite effectiveness
            for prereq in prerequisites:
                if prereq not in remediation_stats["prerequisite_effectiveness"]:
                    remediation_stats["prerequisite_effectiveness"][prereq] = {
                        "total_uses": 0,
                        "total_success_rate": 0.0,
                        "success_count": 0
                    }
                
                stats = remediation_stats["prerequisite_effectiveness"][prereq]
                stats["total_uses"] += 1
                stats["total_success_rate"] += success_rate
                if success_rate > 0.7:
                    stats["success_count"] += 1
        
        # Calculate averages
        if resolution_times:
            remediation_stats["average_resolution_time"] = sum(resolution_times) / len(resolution_times)
        
        # Calculate effectiveness scores
        for mode, stats in remediation_stats["learning_mode_effectiveness"].items():
            if stats["total_uses"] >= 2:
                stats["avg_success_rate"] = stats["total_success_rate"] / stats["total_uses"]
                stats["effectiveness_score"] = (
                    stats["avg_success_rate"] * 0.7 +
                    (stats["success_count"] / stats["total_uses"]) * 0.3
                )
        
        for prereq, stats in remediation_stats["prerequisite_effectiveness"].items():
            if stats["total_uses"] >= 2:
                stats["avg_success_rate"] = stats["total_success_rate"] / stats["total_uses"]
                stats["effectiveness_score"] = (
                    stats["avg_success_rate"] * 0.7 +
                    (stats["success_count"] / stats["total_uses"]) * 0.3
                )
        
        return {
            "gap_type": gap_type,
            "grade_level": grade_level,
            "subject": subject,
            "time_period_days": time_period_days,
            "remediation_stats": remediation_stats,
            "analysis_metadata": {
                "search_query": search_query,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def extract_learning_mode_patterns(
        self,
        gap_type: str,
        grade_level: str,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract learning mode effectiveness patterns from successful remediations.
        """
        logger.info(f"🎮 Extracting learning mode patterns for {gap_type} gaps")
        
        # Search for successful remediation cases
        search_query = f"{gap_type} successful remediation learning modes {grade_level} {subject or ''}"
        query_embedding = await generate_embedding(search_query)
        
        gap_results = await query_vectors(
            "learning_gaps",
            query_embedding,
            top_k=30,
            filter_dict=create_combined_filter(
                grade_level=grade_level,
                subject=subject
            ),
            include_metadata=True
        )
        
        # Filter for successful cases
        successful_cases = [
            result for result in gap_results
            if result.get("metadata", {}).get("remediation_success_rate", 0.0) > 0.7
        ]
        
        # Analyze learning mode sequences
        mode_sequences = {}
        mode_combinations = {}
        individual_mode_effectiveness = {}
        
        for case in successful_cases:
            metadata = case.get("metadata", {})
            learning_modes = metadata.get("learning_modes_used", [])
            success_rate = metadata.get("remediation_success_rate", 0.0)
            
            if not learning_modes:
                continue
            
            # Analyze individual modes
            for mode in learning_modes:
                if mode not in individual_mode_effectiveness:
                    individual_mode_effectiveness[mode] = {
                        "total_uses": 0,
                        "total_success_rate": 0.0,
                        "success_count": 0
                    }
                
                stats = individual_mode_effectiveness[mode]
                stats["total_uses"] += 1
                stats["total_success_rate"] += success_rate
                if success_rate > 0.8:
                    stats["success_count"] += 1
            
            # Analyze mode sequences
            if len(learning_modes) > 1:
                sequence_key = " -> ".join(learning_modes)
                if sequence_key not in mode_sequences:
                    mode_sequences[sequence_key] = {
                        "sequence": learning_modes,
                        "total_uses": 0,
                        "total_success_rate": 0.0,
                        "success_count": 0
                    }
                
                stats = mode_sequences[sequence_key]
                stats["total_uses"] += 1
                stats["total_success_rate"] += success_rate
                if success_rate > 0.8:
                    stats["success_count"] += 1
            
            # Analyze mode combinations (order doesn't matter)
            if len(learning_modes) > 1:
                combination_key = " + ".join(sorted(learning_modes))
                if combination_key not in mode_combinations:
                    mode_combinations[combination_key] = {
                        "modes": sorted(learning_modes),
                        "total_uses": 0,
                        "total_success_rate": 0.0,
                        "success_count": 0
                    }
                
                stats = mode_combinations[combination_key]
                stats["total_uses"] += 1
                stats["total_success_rate"] += success_rate
                if success_rate > 0.8:
                    stats["success_count"] += 1
        
        # Calculate effectiveness scores
        def calculate_effectiveness(stats):
            if stats["total_uses"] >= 2:
                stats["avg_success_rate"] = stats["total_success_rate"] / stats["total_uses"]
                stats["effectiveness_score"] = (
                    stats["avg_success_rate"] * 0.6 +
                    (stats["success_count"] / stats["total_uses"]) * 0.4
                )
                return stats
            return None
        
        # Process individual modes
        effective_individual_modes = []
        for mode, stats in individual_mode_effectiveness.items():
            processed_stats = calculate_effectiveness(stats)
            if processed_stats:
                processed_stats["mode"] = mode
                effective_individual_modes.append(processed_stats)
        
        # Process mode sequences
        effective_sequences = []
        for sequence_key, stats in mode_sequences.items():
            processed_stats = calculate_effectiveness(stats)
            if processed_stats:
                effective_sequences.append(processed_stats)
        
        # Process mode combinations
        effective_combinations = []
        for combination_key, stats in mode_combinations.items():
            processed_stats = calculate_effectiveness(stats)
            if processed_stats:
                effective_combinations.append(processed_stats)
        
        # Sort by effectiveness
        effective_individual_modes.sort(key=lambda x: x["effectiveness_score"], reverse=True)
        effective_sequences.sort(key=lambda x: x["effectiveness_score"], reverse=True)
        effective_combinations.sort(key=lambda x: x["effectiveness_score"], reverse=True)
        
        return {
            "gap_type": gap_type,
            "grade_level": grade_level,
            "subject": subject,
            "total_successful_cases": len(successful_cases),
            "individual_mode_effectiveness": effective_individual_modes[:10],
            "effective_sequences": effective_sequences[:5],
            "effective_combinations": effective_combinations[:5],
            "analysis_metadata": {
                "search_query": search_query,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def get_collaborative_learning_recommendations(
        self,
        student_id: str,
        learning_gaps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get recommendations for collaborative learning based on similar students.
        """
        logger.info(f"👥 Getting collaborative learning recommendations for student: {student_id}")
        
        # Find similar students
        similar_students_result = await self.find_similar_students(
            student_id, learning_gaps, max_recommendations=5
        )
        
        similar_students = similar_students_result.get("similar_students", [])
        
        if not similar_students:
            return {
                "student_id": student_id,
                "collaborative_recommendations": [],
                "message": "No similar students found for collaborative learning"
            }
        
        # Analyze successful remediation strategies from similar students
        successful_strategies = []
        for similar_student in similar_students:
            student_id_found = similar_student["student_id"]
            
            # Get successful remediation cases for this student
            try:
                def _get_student_reports():
                    return list(student_reports_collection.find({
                        "studentId": student_id_found,
                        "report.remedy_report": {"$exists": True, "$ne": []}
                    }, {
                        "report.remedy_report": 1,
                        "studentId": 1
                    }))
                
                student_reports = await anyio.to_thread.run_sync(_get_student_reports)
                
                for report in student_reports:
                    remedy_reports = report.get("report", {}).get("remedy_report", [])
                    for remedy_entry in remedy_reports:
                        if remedy_entry.get("success_rate", 0.0) > 0.7:  # Successful case
                            successful_strategies.append({
                                "student_id": student_id_found,
                                "gap_code": remedy_entry.get("gap_code", ""),
                                "gap_type": remedy_entry.get("gap_type", ""),
                                "success_rate": remedy_entry.get("success_rate", 0.0),
                                "learning_modes_used": remedy_entry.get("learning_modes_used", []),
                                "prerequisites": remedy_entry.get("prerequisites", []),
                                "time_to_resolve": remedy_entry.get("time_to_resolve_hours", 0.0)
                            })
            except Exception as e:
                logger.warning(f"Error getting reports for student {student_id_found}: {e}")
        
        # Group strategies by gap type
        strategies_by_gap_type = {}
        for strategy in successful_strategies:
            gap_type = strategy["gap_type"]
            if gap_type not in strategies_by_gap_type:
                strategies_by_gap_type[gap_type] = []
            strategies_by_gap_type[gap_type].append(strategy)
        
        # Create collaborative learning recommendations
        collaborative_recommendations = []
        for gap_type, strategies in strategies_by_gap_type.items():
            if strategies:
                # Find most effective strategies for this gap type
                strategies.sort(key=lambda x: x["success_rate"], reverse=True)
                top_strategy = strategies[0]
                
                # Find students who used this strategy successfully
                successful_students = [
                    s["student_id"] for s in strategies[:3]
                    if s["success_rate"] > 0.7
                ]
                
                collaborative_recommendations.append({
                    "gap_type": gap_type,
                    "recommended_strategy": {
                        "learning_modes": top_strategy["learning_modes_used"],
                        "prerequisites": top_strategy["prerequisites"],
                        "expected_success_rate": top_strategy["success_rate"],
                        "estimated_time_hours": top_strategy["time_to_resolve"]
                    },
                    "collaborative_partners": successful_students,
                    "strategy_evidence_count": len(strategies)
                })
        
        return {
            "student_id": student_id,
            "collaborative_recommendations": collaborative_recommendations,
            "similar_students_count": len(similar_students),
            "total_strategies_analyzed": len(successful_strategies),
            "analysis_metadata": {
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _create_student_profile_text(self, learning_gaps: List[Dict[str, Any]]) -> str:
        """Create text representation of student learning profile."""
        gap_codes = [gap.get("code", "") for gap in learning_gaps]
        gap_types = [gap.get("type", "") for gap in learning_gaps]
        evidence = []
        
        for gap in learning_gaps:
            if gap.get("evidence"):
                evidence.extend(gap["evidence"])
        
        profile_parts = [
            f"Learning gaps: {', '.join(gap_codes)}",
            f"Gap types: {', '.join(gap_types)}"
        ]
        
        if evidence:
            profile_parts.append(f"Evidence: {', '.join(evidence[:5])}")  # Limit evidence
        
        return ". ".join(profile_parts)

# Global analyzer instance
similar_gap_analyzer = SimilarGapAnalyzer()

# Convenience functions for easy access
async def find_similar_students(
    student_id: str,
    learning_gaps: List[Dict[str, Any]],
    max_recommendations: int = 5,
    min_similarity_threshold: float = 0.7
) -> Dict[str, Any]:
    """Find students with similar learning patterns."""
    return await similar_gap_analyzer.find_similar_students(
        student_id, learning_gaps, max_recommendations, min_similarity_threshold
    )

async def analyze_remediation_effectiveness(
    gap_type: str,
    grade_level: str,
    subject: Optional[str] = None,
    time_period_days: int = 90
) -> Dict[str, Any]:
    """Analyze remediation effectiveness for specific gap types."""
    return await similar_gap_analyzer.analyze_remediation_effectiveness(
        gap_type, grade_level, subject, time_period_days
    )

async def extract_learning_mode_patterns(
    gap_type: str,
    grade_level: str,
    subject: Optional[str] = None
) -> Dict[str, Any]:
    """Extract learning mode effectiveness patterns."""
    return await similar_gap_analyzer.extract_learning_mode_patterns(
        gap_type, grade_level, subject
    )

async def get_collaborative_learning_recommendations(
    student_id: str,
    learning_gaps: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Get collaborative learning recommendations."""
    return await similar_gap_analyzer.get_collaborative_learning_recommendations(
        student_id, learning_gaps
    )
