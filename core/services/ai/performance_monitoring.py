"""
Performance Monitoring for RAG System
Tracks and analyzes system performance, accuracy, and effectiveness.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import time
import json

from core.services.ai.pinecone_client import get_index_stats, is_pinecone_available
from core.services.ai.enhanced_rag_integration import enhanced_rag
from core.services.ai.content_recommendation_engine import recommendation_engine
from core.services.ai.similar_gap_analysis import similar_gap_analyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PerformanceMonitor:
    """
    Monitors and analyzes RAG system performance.
    Tracks metrics for optimization and A/B testing.
    """
    
    def __init__(self):
        self.metrics_store = {}
        self.performance_cache = {}
        self.cache_ttl = 300  # 5 minutes
    
    async def track_vector_search_performance(
        self,
        query: str,
        index_name: str,
        response_time: float,
        result_count: int,
        success: bool
    ):
        """Track vector search performance metrics."""
        metric_key = f"vector_search_{index_name}"
        
        if metric_key not in self.metrics_store:
            self.metrics_store[metric_key] = {
                "total_queries": 0,
                "successful_queries": 0,
                "total_response_time": 0.0,
                "avg_response_time": 0.0,
                "total_results": 0,
                "avg_results_per_query": 0.0,
                "response_times": [],
                "result_counts": []
            }
        
        metrics = self.metrics_store[metric_key]
        metrics["total_queries"] += 1
        metrics["total_response_time"] += response_time
        metrics["total_results"] += result_count
        metrics["response_times"].append(response_time)
        metrics["result_counts"].append(result_count)
        
        if success:
            metrics["successful_queries"] += 1
        
        # Calculate averages
        metrics["avg_response_time"] = metrics["total_response_time"] / metrics["total_queries"]
        metrics["avg_results_per_query"] = metrics["total_results"] / metrics["total_queries"]
        
        # Keep only recent data (last 100 queries)
        if len(metrics["response_times"]) > 100:
            metrics["response_times"] = metrics["response_times"][-100:]
            metrics["result_counts"] = metrics["result_counts"][-100:]
        
        logger.info(f"📊 Tracked vector search: {index_name} - {response_time:.3f}s, {result_count} results")
    
    async def track_prerequisite_discovery_performance(
        self,
        gap_code: str,
        grade_level: str,
        response_time: float,
        prerequisites_found: int,
        source: str,  # "vector_search", "llm_fallback", "cached"
        success: bool
    ):
        """Track prerequisite discovery performance."""
        metric_key = "prerequisite_discovery"
        
        if metric_key not in self.metrics_store:
            self.metrics_store[metric_key] = {
                "total_requests": 0,
                "successful_requests": 0,
                "total_response_time": 0.0,
                "avg_response_time": 0.0,
                "total_prerequisites": 0,
                "avg_prerequisites_per_request": 0.0,
                "source_breakdown": {
                    "vector_search": {"count": 0, "avg_time": 0.0, "avg_prereqs": 0.0},
                    "llm_fallback": {"count": 0, "avg_time": 0.0, "avg_prereqs": 0.0},
                    "cached": {"count": 0, "avg_time": 0.0, "avg_prereqs": 0.0}
                }
            }
        
        metrics = self.metrics_store[metric_key]
        metrics["total_requests"] += 1
        metrics["total_response_time"] += response_time
        metrics["total_prerequisites"] += prerequisites_found
        
        if success:
            metrics["successful_requests"] += 1
        
        # Update source breakdown
        if source in metrics["source_breakdown"]:
            source_metrics = metrics["source_breakdown"][source]
            source_metrics["count"] += 1
            source_metrics["avg_time"] = (
                (source_metrics["avg_time"] * (source_metrics["count"] - 1) + response_time) / 
                source_metrics["count"]
            )
            source_metrics["avg_prereqs"] = (
                (source_metrics["avg_prereqs"] * (source_metrics["count"] - 1) + prerequisites_found) / 
                source_metrics["count"]
            )
        
        # Calculate overall averages
        metrics["avg_response_time"] = metrics["total_response_time"] / metrics["total_requests"]
        metrics["avg_prerequisites_per_request"] = metrics["total_prerequisites"] / metrics["total_requests"]
        
        logger.info(f"📊 Tracked prerequisite discovery: {gap_code} - {response_time:.3f}s, {prerequisites_found} prereqs via {source}")
    
    async def track_content_recommendation_performance(
        self,
        recommendation_type: str,
        response_time: float,
        recommendations_count: int,
        user_satisfaction: Optional[float] = None
    ):
        """Track content recommendation performance."""
        metric_key = f"content_recommendation_{recommendation_type}"
        
        if metric_key not in self.metrics_store:
            self.metrics_store[metric_key] = {
                "total_requests": 0,
                "total_response_time": 0.0,
                "avg_response_time": 0.0,
                "total_recommendations": 0,
                "avg_recommendations_per_request": 0.0,
                "user_satisfaction_scores": [],
                "avg_user_satisfaction": 0.0
            }
        
        metrics = self.metrics_store[metric_key]
        metrics["total_requests"] += 1
        metrics["total_response_time"] += response_time
        metrics["total_recommendations"] += recommendations_count
        
        if user_satisfaction is not None:
            metrics["user_satisfaction_scores"].append(user_satisfaction)
            metrics["avg_user_satisfaction"] = sum(metrics["user_satisfaction_scores"]) / len(metrics["user_satisfaction_scores"])
        
        # Calculate averages
        metrics["avg_response_time"] = metrics["total_response_time"] / metrics["total_requests"]
        metrics["avg_recommendations_per_request"] = metrics["total_recommendations"] / metrics["total_requests"]
        
        logger.info(f"📊 Tracked content recommendation: {recommendation_type} - {response_time:.3f}s, {recommendations_count} recommendations")
    
    async def track_remediation_success_rate(
        self,
        gap_type: str,
        grade_level: str,
        remediation_plan: Dict[str, Any],
        success_rate: float,
        duration_hours: float
    ):
        """Track remediation success rates for optimization."""
        metric_key = f"remediation_success_{gap_type}_{grade_level}"
        
        if metric_key not in self.metrics_store:
            self.metrics_store[metric_key] = {
                "total_remediations": 0,
                "successful_remediations": 0,
                "total_duration": 0.0,
                "avg_duration": 0.0,
                "success_rates": [],
                "avg_success_rate": 0.0,
                "learning_mode_effectiveness": {},
                "prerequisite_effectiveness": {}
            }
        
        metrics = self.metrics_store[metric_key]
        metrics["total_remediations"] += 1
        metrics["total_duration"] += duration_hours
        metrics["success_rates"].append(success_rate)
        
        if success_rate > 0.7:  # Consider >70% as successful
            metrics["successful_remediations"] += 1
        
        # Calculate averages
        metrics["avg_duration"] = metrics["total_duration"] / metrics["total_remediations"]
        metrics["avg_success_rate"] = sum(metrics["success_rates"]) / len(metrics["success_rates"])
        
        # Track learning mode effectiveness
        learning_modes = remediation_plan.get("selected_modes", [])
        for mode in learning_modes:
            if mode not in metrics["learning_mode_effectiveness"]:
                metrics["learning_mode_effectiveness"][mode] = {
                    "total_uses": 0,
                    "total_success_rate": 0.0,
                    "success_count": 0
                }
            
            mode_stats = metrics["learning_mode_effectiveness"][mode]
            mode_stats["total_uses"] += 1
            mode_stats["total_success_rate"] += success_rate
            if success_rate > 0.7:
                mode_stats["success_count"] += 1
        
        # Track prerequisite effectiveness
        prerequisites = remediation_plan.get("prerequisites", [])
        for prereq in prerequisites:
            prereq_topic = prereq.get("topic", "unknown")
            if prereq_topic not in metrics["prerequisite_effectiveness"]:
                metrics["prerequisite_effectiveness"][prereq_topic] = {
                    "total_uses": 0,
                    "total_success_rate": 0.0,
                    "success_count": 0
                }
            
            prereq_stats = metrics["prerequisite_effectiveness"][prereq_topic]
            prereq_stats["total_uses"] += 1
            prereq_stats["total_success_rate"] += success_rate
            if success_rate > 0.7:
                prereq_stats["success_count"] += 1
        
        logger.info(f"📊 Tracked remediation success: {gap_type} - {success_rate:.1%} success in {duration_hours:.1f}h")
    
    async def get_system_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive system performance summary."""
        logger.info("📈 Generating system performance summary")
        
        # Get vector database stats
        vector_db_stats = {}
        if is_pinecone_available():
            for index_name in ["educational_content", "learning_gaps", "prerequisites"]:
                try:
                    stats = await get_index_stats(index_name)
                    if stats:
                        vector_db_stats[index_name] = stats
                except Exception as e:
                    logger.warning(f"Could not get stats for {index_name}: {e}")
        
        # Calculate overall performance metrics
        performance_summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "vector_database_stats": vector_db_stats,
            "performance_metrics": self.metrics_store,
            "system_health": await self._calculate_system_health(),
            "recommendations": await self._generate_performance_recommendations()
        }
        
        return performance_summary
    
    async def _calculate_system_health(self) -> Dict[str, Any]:
        """Calculate overall system health score."""
        health_score = 100.0
        health_issues = []
        
        # Check vector search performance
        for metric_key, metrics in self.metrics_store.items():
            if metric_key.startswith("vector_search_"):
                if metrics["avg_response_time"] > 2.0:  # >2 seconds is slow
                    health_score -= 10
                    health_issues.append(f"Slow vector search in {metric_key}: {metrics['avg_response_time']:.2f}s")
                
                success_rate = metrics["successful_queries"] / metrics["total_queries"] if metrics["total_queries"] > 0 else 0
                if success_rate < 0.9:  # <90% success rate
                    health_score -= 15
                    health_issues.append(f"Low vector search success rate in {metric_key}: {success_rate:.1%}")
        
        # Check prerequisite discovery performance
        if "prerequisite_discovery" in self.metrics_store:
            prereq_metrics = self.metrics_store["prerequisite_discovery"]
            if prereq_metrics["avg_response_time"] > 3.0:  # >3 seconds is slow
                health_score -= 10
                health_issues.append(f"Slow prerequisite discovery: {prereq_metrics['avg_response_time']:.2f}s")
            
            success_rate = prereq_metrics["successful_requests"] / prereq_metrics["total_requests"] if prereq_metrics["total_requests"] > 0 else 0
            if success_rate < 0.8:  # <80% success rate
                health_score -= 20
                health_issues.append(f"Low prerequisite discovery success rate: {success_rate:.1%}")
        
        # Check content recommendation performance
        for metric_key, metrics in self.metrics_store.items():
            if metric_key.startswith("content_recommendation_"):
                if metrics["avg_response_time"] > 1.5:  # >1.5 seconds is slow
                    health_score -= 5
                    health_issues.append(f"Slow content recommendation in {metric_key}: {metrics['avg_response_time']:.2f}s")
        
        # Check remediation success rates
        for metric_key, metrics in self.metrics_store.items():
            if metric_key.startswith("remediation_success_"):
                if metrics["avg_success_rate"] < 0.6:  # <60% success rate
                    health_score -= 15
                    health_issues.append(f"Low remediation success rate in {metric_key}: {metrics['avg_success_rate']:.1%}")
        
        return {
            "overall_score": max(0, health_score),
            "status": "healthy" if health_score >= 80 else "degraded" if health_score >= 60 else "critical",
            "issues": health_issues
        }
    
    async def _generate_performance_recommendations(self) -> List[Dict[str, Any]]:
        """Generate performance optimization recommendations."""
        recommendations = []
        
        # Analyze vector search performance
        for metric_key, metrics in self.metrics_store.items():
            if metric_key.startswith("vector_search_"):
                if metrics["avg_response_time"] > 1.0:
                    recommendations.append({
                        "type": "performance",
                        "priority": "high",
                        "category": "vector_search",
                        "metric": metric_key,
                        "issue": f"Slow response time: {metrics['avg_response_time']:.2f}s",
                        "recommendation": "Consider optimizing embedding generation or reducing query complexity",
                        "expected_improvement": "20-30% faster response times"
                    })
                
                if metrics["avg_results_per_query"] < 5:
                    recommendations.append({
                        "type": "effectiveness",
                        "priority": "medium",
                        "category": "vector_search",
                        "metric": metric_key,
                        "issue": f"Low result count: {metrics['avg_results_per_query']:.1f} results per query",
                        "recommendation": "Consider adjusting similarity thresholds or expanding search scope",
                        "expected_improvement": "More comprehensive search results"
                    })
        
        # Analyze prerequisite discovery performance
        if "prerequisite_discovery" in self.metrics_store:
            prereq_metrics = self.metrics_store["prerequisite_discovery"]
            vector_search_usage = prereq_metrics["source_breakdown"]["vector_search"]["count"]
            total_requests = prereq_metrics["total_requests"]
            
            if total_requests > 0 and (vector_search_usage / total_requests) < 0.5:
                recommendations.append({
                    "type": "optimization",
                    "priority": "medium",
                    "category": "prerequisite_discovery",
                    "issue": f"Low vector search usage: {vector_search_usage/total_requests:.1%}",
                    "recommendation": "Improve vector search coverage or fallback logic",
                    "expected_improvement": "More accurate prerequisite discovery"
                })
        
        # Analyze remediation success rates
        for metric_key, metrics in self.metrics_store.items():
            if metric_key.startswith("remediation_success_"):
                if metrics["avg_success_rate"] < 0.7:
                    recommendations.append({
                        "type": "effectiveness",
                        "priority": "high",
                        "category": "remediation",
                        "metric": metric_key,
                        "issue": f"Low success rate: {metrics['avg_success_rate']:.1%}",
                        "recommendation": "Review and optimize learning mode sequences and prerequisites",
                        "expected_improvement": "10-20% improvement in success rates"
                    })
        
        return recommendations
    
    async def run_ab_test(
        self,
        test_name: str,
        variant_a: Dict[str, Any],
        variant_b: Dict[str, Any],
        test_duration_hours: int = 24
    ) -> Dict[str, Any]:
        """Run A/B test for performance comparison."""
        logger.info(f"🧪 Starting A/B test: {test_name}")
        
        test_start = datetime.utcnow()
        test_end = test_start + timedelta(hours=test_duration_hours)
        
        # Initialize test metrics
        test_metrics = {
            "test_name": test_name,
            "start_time": test_start.isoformat(),
            "end_time": test_end.isoformat(),
            "variant_a": {
                "config": variant_a,
                "requests": 0,
                "successes": 0,
                "avg_response_time": 0.0,
                "user_satisfaction": []
            },
            "variant_b": {
                "config": variant_b,
                "requests": 0,
                "successes": 0,
                "avg_response_time": 0.0,
                "user_satisfaction": []
            }
        }
        
        # Store test configuration
        self.metrics_store[f"ab_test_{test_name}"] = test_metrics
        
        return {
            "test_id": test_name,
            "status": "started",
            "duration_hours": test_duration_hours,
            "variants": ["A", "B"]
        }
    
    async def record_ab_test_result(
        self,
        test_name: str,
        variant: str,
        success: bool,
        response_time: float,
        user_satisfaction: Optional[float] = None
    ):
        """Record A/B test result."""
        test_key = f"ab_test_{test_name}"
        
        if test_key not in self.metrics_store:
            logger.warning(f"A/B test {test_name} not found")
            return
        
        test_metrics = self.metrics_store[test_key]
        variant_key = f"variant_{variant.lower()}"
        
        if variant_key not in test_metrics:
            logger.warning(f"Variant {variant} not found in test {test_name}")
            return
        
        variant_metrics = test_metrics[variant_key]
        variant_metrics["requests"] += 1
        
        if success:
            variant_metrics["successes"] += 1
        
        # Update average response time
        variant_metrics["avg_response_time"] = (
            (variant_metrics["avg_response_time"] * (variant_metrics["requests"] - 1) + response_time) / 
            variant_metrics["requests"]
        )
        
        if user_satisfaction is not None:
            variant_metrics["user_satisfaction"].append(user_satisfaction)
        
        logger.info(f"📊 Recorded A/B test result: {test_name} variant {variant} - success: {success}, time: {response_time:.3f}s")

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Convenience functions for easy access
async def track_vector_search_performance(
    query: str,
    index_name: str,
    response_time: float,
    result_count: int,
    success: bool
):
    """Track vector search performance."""
    await performance_monitor.track_vector_search_performance(
        query, index_name, response_time, result_count, success
    )

async def track_prerequisite_discovery_performance(
    gap_code: str,
    grade_level: str,
    response_time: float,
    prerequisites_found: int,
    source: str,
    success: bool
):
    """Track prerequisite discovery performance."""
    await performance_monitor.track_prerequisite_discovery_performance(
        gap_code, grade_level, response_time, prerequisites_found, source, success
    )

async def track_content_recommendation_performance(
    recommendation_type: str,
    response_time: float,
    recommendations_count: int,
    user_satisfaction: Optional[float] = None
):
    """Track content recommendation performance."""
    await performance_monitor.track_content_recommendation_performance(
        recommendation_type, response_time, recommendations_count, user_satisfaction
    )

async def track_remediation_success_rate(
    gap_type: str,
    grade_level: str,
    remediation_plan: Dict[str, Any],
    success_rate: float,
    duration_hours: float
):
    """Track remediation success rate."""
    await performance_monitor.track_remediation_success_rate(
        gap_type, grade_level, remediation_plan, success_rate, duration_hours
    )

async def get_system_performance_summary() -> Dict[str, Any]:
    """Get system performance summary."""
    return await performance_monitor.get_system_performance_summary()

async def run_ab_test(
    test_name: str,
    variant_a: Dict[str, Any],
    variant_b: Dict[str, Any],
    test_duration_hours: int = 24
) -> Dict[str, Any]:
    """Run A/B test."""
    return await performance_monitor.run_ab_test(
        test_name, variant_a, variant_b, test_duration_hours
    )
