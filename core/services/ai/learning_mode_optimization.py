"""
Learning Mode Optimization for RAG System
Analyzes and optimizes learning mode sequences for maximum effectiveness.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import anyio

from core.services.ai.pinecone_client import query_vectors, generate_embedding
from core.services.ai.vector_schemas import create_combined_filter
from core.services.ai.similar_gap_analysis import similar_gap_analyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LearningModeOptimizer:
    """
    Optimizes learning mode sequences based on historical success patterns.
    Provides data-driven recommendations for maximum remediation effectiveness.
    """
    
    def __init__(self):
        self.optimization_cache = {}
        self.cache_ttl = 900  # 15 minutes
    
    async def optimize_learning_mode_sequence(
        self,
        gap_type: str,
        grade_level: str,
        subject: str,
        student_profile: Optional[Dict[str, Any]] = None,
        max_modes: int = 5
    ) -> Dict[str, Any]:
        """
        Optimize learning mode sequence for a specific gap type and student profile.
        """
        logger.info(f"🎯 Optimizing learning mode sequence for {gap_type} gaps")
        
        # Get learning mode patterns from similar gap analysis
        mode_patterns = await similar_gap_analyzer.extract_learning_mode_patterns(
            gap_type, grade_level, subject
        )
        
        # Get remediation effectiveness data
        effectiveness_data = await similar_gap_analyzer.analyze_remediation_effectiveness(
            gap_type, grade_level, subject
        )
        
        # Extract mode effectiveness data
        mode_effectiveness = effectiveness_data.get("remediation_stats", {}).get("learning_mode_effectiveness", {})
        
        # Create optimized sequence
        optimized_sequence = await self._create_optimized_sequence(
            mode_patterns, mode_effectiveness, student_profile, max_modes
        )
        
        # Calculate expected effectiveness
        expected_effectiveness = await self._calculate_expected_effectiveness(
            optimized_sequence, mode_patterns, mode_effectiveness
        )
        
        return {
            "gap_type": gap_type,
            "grade_level": grade_level,
            "subject": subject,
            "optimized_sequence": optimized_sequence,
            "expected_effectiveness": expected_effectiveness,
            "optimization_metadata": {
                "patterns_analyzed": mode_patterns.get("total_successful_cases", 0),
                "effectiveness_data_points": len(mode_effectiveness),
                "student_profile_applied": bool(student_profile),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def _create_optimized_sequence(
        self,
        mode_patterns: Dict[str, Any],
        mode_effectiveness: Dict[str, Any],
        student_profile: Optional[Dict[str, Any]],
        max_modes: int
    ) -> List[Dict[str, Any]]:
        """Create optimized learning mode sequence."""
        
        # Get effective individual modes
        individual_modes = mode_patterns.get("individual_mode_effectiveness", [])
        
        # Get effective sequences
        effective_sequences = mode_patterns.get("effective_sequences", [])
        
        # Get effective combinations
        effective_combinations = mode_patterns.get("effective_combinations", [])
        
        # Score and rank all possible modes
        mode_scores = {}
        
        # Score individual modes
        for mode_data in individual_modes:
            mode = mode_data["mode"]
            score = mode_data["effectiveness_score"]
            
            # Apply student profile preferences
            if student_profile:
                preferred_modes = student_profile.get("preferred_modes", [])
                if mode in preferred_modes:
                    score *= 1.2  # Boost preferred modes
                
                avoided_modes = student_profile.get("avoided_modes", [])
                if mode in avoided_modes:
                    score *= 0.5  # Reduce avoided modes
            
            mode_scores[mode] = {
                "mode": mode,
                "score": score,
                "type": "individual",
                "evidence_count": mode_data["total_uses"],
                "success_rate": mode_data["avg_success_rate"]
            }
        
        # Score mode sequences
        for sequence_data in effective_sequences:
            sequence = sequence_data["sequence"]
            score = sequence_data["effectiveness_score"]
            
            # Apply student profile preferences
            if student_profile:
                preferred_modes = student_profile.get("preferred_modes", [])
                sequence_preference_boost = sum(1 for mode in sequence if mode in preferred_modes) / len(sequence)
                score *= (1 + sequence_preference_boost * 0.1)
            
            sequence_key = " -> ".join(sequence)
            mode_scores[sequence_key] = {
                "mode": sequence,
                "score": score,
                "type": "sequence",
                "evidence_count": sequence_data["total_uses"],
                "success_rate": sequence_data["avg_success_rate"]
            }
        
        # Score mode combinations
        for combination_data in effective_combinations:
            combination = combination_data["modes"]
            score = combination_data["effectiveness_score"]
            
            # Apply student profile preferences
            if student_profile:
                preferred_modes = student_profile.get("preferred_modes", [])
                combination_preference_boost = sum(1 for mode in combination if mode in preferred_modes) / len(combination)
                score *= (1 + combination_preference_boost * 0.1)
            
            combination_key = " + ".join(combination)
            mode_scores[combination_key] = {
                "mode": combination,
                "score": score,
                "type": "combination",
                "evidence_count": combination_data["total_uses"],
                "success_rate": combination_data["avg_success_rate"]
            }
        
        # Sort by score and create optimized sequence
        sorted_modes = sorted(mode_scores.values(), key=lambda x: x["score"], reverse=True)
        
        # Create sequence with diversity and effectiveness balance
        optimized_sequence = []
        used_modes = set()
        
        for mode_data in sorted_modes[:max_modes * 2]:  # Get more options for diversity
            if len(optimized_sequence) >= max_modes:
                break
            
            mode = mode_data["mode"]
            mode_type = mode_data["type"]
            
            # Check for diversity (avoid too many similar modes)
            if mode_type == "individual":
                if mode not in used_modes:
                    optimized_sequence.append({
                        "mode": mode,
                        "type": "individual",
                        "effectiveness_score": mode_data["score"],
                        "evidence_count": mode_data["evidence_count"],
                        "success_rate": mode_data["success_rate"],
                        "rationale": f"Highly effective individual mode with {mode_data['success_rate']:.1%} success rate"
                    })
                    used_modes.add(mode)
            
            elif mode_type == "sequence":
                # Check if sequence modes are already used individually
                sequence_modes = set(mode) if isinstance(mode, list) else {mode}
                if not sequence_modes.intersection(used_modes):
                    optimized_sequence.append({
                        "mode": mode,
                        "type": "sequence",
                        "effectiveness_score": mode_data["score"],
                        "evidence_count": mode_data["evidence_count"],
                        "success_rate": mode_data["success_rate"],
                        "rationale": f"Proven effective sequence with {mode_data['success_rate']:.1%} success rate"
                    })
                    used_modes.update(sequence_modes)
            
            elif mode_type == "combination":
                # Check if combination modes are already used
                combination_modes = set(mode) if isinstance(mode, list) else {mode}
                if not combination_modes.intersection(used_modes):
                    optimized_sequence.append({
                        "mode": mode,
                        "type": "combination",
                        "effectiveness_score": mode_data["score"],
                        "evidence_count": mode_data["evidence_count"],
                        "success_rate": mode_data["success_rate"],
                        "rationale": f"Effective combination with {mode_data['success_rate']:.1%} success rate"
                    })
                    used_modes.update(combination_modes)
        
        return optimized_sequence[:max_modes]
    
    async def _calculate_expected_effectiveness(
        self,
        optimized_sequence: List[Dict[str, Any]],
        mode_patterns: Dict[str, Any],
        mode_effectiveness: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate expected effectiveness of the optimized sequence."""
        
        if not optimized_sequence:
            return {
                "expected_success_rate": 0.0,
                "confidence_level": "low",
                "estimated_duration_hours": 0.0,
                "risk_factors": ["No optimized sequence available"]
            }
        
        # Calculate weighted average success rate
        total_score = 0.0
        total_weight = 0.0
        total_duration = 0.0
        
        for mode_data in optimized_sequence:
            score = mode_data["effectiveness_score"]
            evidence_count = mode_data["evidence_count"]
            
            total_score += score * evidence_count
            total_weight += evidence_count
            
            # Estimate duration based on mode type
            if mode_data["type"] == "individual":
                total_duration += 2.0  # 2 hours per individual mode
            elif mode_data["type"] == "sequence":
                mode_count = len(mode_data["mode"]) if isinstance(mode_data["mode"], list) else 1
                total_duration += mode_count * 1.5  # 1.5 hours per mode in sequence
            elif mode_data["type"] == "combination":
                mode_count = len(mode_data["mode"]) if isinstance(mode_data["mode"], list) else 1
                total_duration += mode_count * 1.0  # 1 hour per mode in combination
        
        expected_success_rate = total_score / total_weight if total_weight > 0 else 0.0
        
        # Determine confidence level
        total_evidence = sum(mode_data["evidence_count"] for mode_data in optimized_sequence)
        if total_evidence >= 20:
            confidence_level = "high"
        elif total_evidence >= 10:
            confidence_level = "medium"
        else:
            confidence_level = "low"
        
        # Identify risk factors
        risk_factors = []
        if expected_success_rate < 0.6:
            risk_factors.append("Low expected success rate")
        if total_evidence < 10:
            risk_factors.append("Limited evidence for optimization")
        if confidence_level == "low":
            risk_factors.append("Low confidence in recommendations")
        
        return {
            "expected_success_rate": expected_success_rate,
            "confidence_level": confidence_level,
            "estimated_duration_hours": total_duration,
            "total_evidence_points": total_evidence,
            "risk_factors": risk_factors
        }
    
    async def get_adaptive_learning_path(
        self,
        student_id: str,
        learning_gaps: List[Dict[str, Any]],
        current_progress: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get adaptive learning path that adjusts based on student progress.
        """
        logger.info(f"🛤️ Creating adaptive learning path for student: {student_id}")
        
        adaptive_path = {
            "student_id": student_id,
            "learning_phases": [],
            "adaptation_points": [],
            "success_metrics": {},
            "fallback_strategies": []
        }
        
        # Group gaps by type for phase-based learning
        gaps_by_type = {}
        for gap in learning_gaps:
            gap_type = gap.get("type", "unknown")
            if gap_type not in gaps_by_type:
                gaps_by_type[gap_type] = []
            gaps_by_type[gap_type].append(gap)
        
        # Create learning phases
        phase_priority = ["foundational", "knowledge", "conceptual", "application", "retention", "engagement"]
        
        for gap_type in phase_priority:
            if gap_type in gaps_by_type:
                gaps = gaps_by_type[gap_type]
                
                # Get optimized sequence for this gap type
                grade_level = gaps[0].get("grade_level", "grade_10")
                subject = gaps[0].get("subject", "mathematics")
                
                optimization_result = await self.optimize_learning_mode_sequence(
                    gap_type, grade_level, subject, max_modes=3
                )
                
                phase = {
                    "phase_name": f"{gap_type.title()} Gap Remediation",
                    "gap_type": gap_type,
                    "gaps": gaps,
                    "optimized_modes": optimization_result["optimized_sequence"],
                    "expected_effectiveness": optimization_result["expected_effectiveness"],
                    "estimated_duration_hours": optimization_result["expected_effectiveness"]["estimated_duration_hours"],
                    "success_criteria": {
                        "min_success_rate": 0.7,
                        "max_duration_hours": optimization_result["expected_effectiveness"]["estimated_duration_hours"] * 1.5
                    }
                }
                
                adaptive_path["learning_phases"].append(phase)
        
        # Add adaptation points
        for i, phase in enumerate(adaptive_path["learning_phases"]):
            adaptation_point = {
                "phase_index": i,
                "phase_name": phase["phase_name"],
                "adaptation_triggers": [
                    "success_rate_below_threshold",
                    "duration_exceeds_estimate",
                    "student_feedback_negative"
                ],
                "adaptation_actions": [
                    "switch_to_alternative_modes",
                    "reduce_mode_complexity",
                    "add_prerequisite_review"
                ]
            }
            adaptive_path["adaptation_points"].append(adaptation_point)
        
        # Add fallback strategies
        adaptive_path["fallback_strategies"] = [
            {
                "trigger": "all_optimized_modes_fail",
                "strategy": "use_individual_high_success_modes",
                "description": "Fall back to individual modes with highest success rates"
            },
            {
                "trigger": "student_engagement_low",
                "strategy": "switch_to_interactive_modes",
                "description": "Switch to more interactive and engaging learning modes"
            },
            {
                "trigger": "time_constraints",
                "strategy": "focus_on_critical_gaps",
                "description": "Focus only on the most critical learning gaps"
            }
        ]
        
        return adaptive_path
    
    async def analyze_mode_effectiveness_trends(
        self,
        time_period_days: int = 30,
        grade_level: Optional[str] = None,
        subject: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze trends in learning mode effectiveness over time.
        """
        logger.info(f"📈 Analyzing learning mode effectiveness trends over {time_period_days} days")
        
        # Create search query for recent data
        search_query = f"recent learning mode effectiveness trends {grade_level or ''} {subject or ''}"
        query_embedding = await generate_embedding(search_query)
        
        # Search for recent learning gap data
        gap_results = await query_vectors(
            "learning_gaps",
            query_embedding,
            top_k=100,
            filter_dict=create_combined_filter(
                grade_level=grade_level,
                subject=subject
            ),
            include_metadata=True
        )
        
        # Filter by time period
        cutoff_date = datetime.utcnow() - timedelta(days=time_period_days)
        recent_gaps = [
            result for result in gap_results
            if result.get("metadata", {}).get("created_at", "") >= cutoff_date.isoformat()
        ]
        
        # Analyze trends by time periods
        time_periods = []
        for i in range(0, time_period_days, 7):  # Weekly periods
            period_start = cutoff_date + timedelta(days=i)
            period_end = period_start + timedelta(days=7)
            
            period_gaps = [
                gap for gap in recent_gaps
                if period_start.isoformat() <= gap.get("metadata", {}).get("created_at", "") < period_end.isoformat()
            ]
            
            if period_gaps:
                period_analysis = self._analyze_period_effectiveness(period_gaps)
                time_periods.append({
                    "period_start": period_start.isoformat(),
                    "period_end": period_end.isoformat(),
                    "gap_count": len(period_gaps),
                    "analysis": period_analysis
                })
        
        # Calculate trends
        trends = self._calculate_effectiveness_trends(time_periods)
        
        return {
            "time_period_days": time_period_days,
            "grade_level": grade_level,
            "subject": subject,
            "total_gaps_analyzed": len(recent_gaps),
            "time_periods": time_periods,
            "trends": trends,
            "analysis_metadata": {
                "search_query": search_query,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _analyze_period_effectiveness(self, period_gaps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze effectiveness for a specific time period."""
        mode_effectiveness = {}
        total_success_rate = 0.0
        successful_cases = 0
        
        for gap in period_gaps:
            metadata = gap.get("metadata", {})
            success_rate = metadata.get("remediation_success_rate", 0.0)
            learning_modes = metadata.get("learning_modes_used", [])
            
            total_success_rate += success_rate
            if success_rate > 0.7:
                successful_cases += 1
            
            for mode in learning_modes:
                if mode not in mode_effectiveness:
                    mode_effectiveness[mode] = {
                        "total_uses": 0,
                        "total_success_rate": 0.0,
                        "success_count": 0
                    }
                
                stats = mode_effectiveness[mode]
                stats["total_uses"] += 1
                stats["total_success_rate"] += success_rate
                if success_rate > 0.7:
                    stats["success_count"] += 1
        
        # Calculate averages
        avg_success_rate = total_success_rate / len(period_gaps) if period_gaps else 0.0
        success_percentage = (successful_cases / len(period_gaps)) * 100 if period_gaps else 0.0
        
        # Calculate mode effectiveness scores
        for mode, stats in mode_effectiveness.items():
            if stats["total_uses"] >= 2:
                stats["avg_success_rate"] = stats["total_success_rate"] / stats["total_uses"]
                stats["effectiveness_score"] = (
                    stats["avg_success_rate"] * 0.7 +
                    (stats["success_count"] / stats["total_uses"]) * 0.3
                )
        
        return {
            "total_gaps": len(period_gaps),
            "avg_success_rate": avg_success_rate,
            "success_percentage": success_percentage,
            "mode_effectiveness": mode_effectiveness
        }
    
    def _calculate_effectiveness_trends(self, time_periods: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate trends across time periods."""
        if len(time_periods) < 2:
            return {"trend": "insufficient_data", "message": "Need at least 2 time periods for trend analysis"}
        
        # Calculate overall success rate trend
        success_rates = [period["analysis"]["avg_success_rate"] for period in time_periods]
        success_rate_trend = "improving" if success_rates[-1] > success_rates[0] else "declining"
        
        # Calculate mode effectiveness trends
        mode_trends = {}
        all_modes = set()
        for period in time_periods:
            all_modes.update(period["analysis"]["mode_effectiveness"].keys())
        
        for mode in all_modes:
            mode_scores = []
            for period in time_periods:
                mode_data = period["analysis"]["mode_effectiveness"].get(mode, {})
                if mode_data.get("effectiveness_score"):
                    mode_scores.append(mode_data["effectiveness_score"])
            
            if len(mode_scores) >= 2:
                mode_trend = "improving" if mode_scores[-1] > mode_scores[0] else "declining"
                mode_trends[mode] = {
                    "trend": mode_trend,
                    "score_change": mode_scores[-1] - mode_scores[0],
                    "current_score": mode_scores[-1]
                }
        
        return {
            "overall_success_rate_trend": success_rate_trend,
            "mode_trends": mode_trends,
            "periods_analyzed": len(time_periods)
        }

# Global optimizer instance
learning_mode_optimizer = LearningModeOptimizer()

# Convenience functions for easy access
async def optimize_learning_mode_sequence(
    gap_type: str,
    grade_level: str,
    subject: str,
    student_profile: Optional[Dict[str, Any]] = None,
    max_modes: int = 5
) -> Dict[str, Any]:
    """Optimize learning mode sequence for a gap type."""
    return await learning_mode_optimizer.optimize_learning_mode_sequence(
        gap_type, grade_level, subject, student_profile, max_modes
    )

async def get_adaptive_learning_path(
    student_id: str,
    learning_gaps: List[Dict[str, Any]],
    current_progress: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Get adaptive learning path for a student."""
    return await learning_mode_optimizer.get_adaptive_learning_path(
        student_id, learning_gaps, current_progress
    )

async def analyze_mode_effectiveness_trends(
    time_period_days: int = 30,
    grade_level: Optional[str] = None,
    subject: Optional[str] = None
) -> Dict[str, Any]:
    """Analyze learning mode effectiveness trends."""
    return await learning_mode_optimizer.analyze_mode_effectiveness_trends(
        time_period_days, grade_level, subject
    )
