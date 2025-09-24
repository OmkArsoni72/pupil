"""
Performance Dashboard API
Provides endpoints for monitoring and analyzing RAG system performance.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from services.ai.performance_monitoring import (
    performance_monitor,
    get_system_performance_summary,
    run_ab_test
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router for performance dashboard
router = APIRouter(prefix="/performance", tags=["performance"])

@router.get("/health")
async def get_system_health():
    """Get overall system health status."""
    try:
        summary = await get_system_performance_summary()
        return {
            "status": "success",
            "data": summary["system_health"],
            "timestamp": summary["timestamp"]
        }
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/metrics")
async def get_performance_metrics(
    metric_type: Optional[str] = Query(None, description="Filter by metric type"),
    time_range_hours: int = Query(24, description="Time range in hours")
):
    """Get performance metrics."""
    try:
        summary = await get_system_performance_summary()
        metrics = summary["performance_metrics"]
        
        if metric_type:
            # Filter by metric type
            filtered_metrics = {}
            for key, value in metrics.items():
                if key.startswith(metric_type):
                    filtered_metrics[key] = value
            metrics = filtered_metrics
        
        return {
            "status": "success",
            "data": metrics,
            "timestamp": summary["timestamp"]
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/vector-db-stats")
async def get_vector_database_stats():
    """Get vector database statistics."""
    try:
        summary = await get_system_performance_summary()
        return {
            "status": "success",
            "data": summary["vector_database_stats"],
            "timestamp": summary["timestamp"]
        }
    except Exception as e:
        logger.error(f"Error getting vector database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations")
async def get_performance_recommendations():
    """Get performance optimization recommendations."""
    try:
        summary = await get_system_performance_summary()
        return {
            "status": "success",
            "data": summary["recommendations"],
            "timestamp": summary["timestamp"]
        }
    except Exception as e:
        logger.error(f"Error getting performance recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ab-test")
async def start_ab_test(
    test_name: str,
    variant_a: Dict[str, Any],
    variant_b: Dict[str, Any],
    test_duration_hours: int = 24
):
    """Start a new A/B test."""
    try:
        result = await run_ab_test(
            test_name, variant_a, variant_b, test_duration_hours
        )
        return {
            "status": "success",
            "data": result
        }
    except Exception as e:
        logger.error(f"Error starting A/B test: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ab-test/{test_name}")
async def get_ab_test_results(test_name: str):
    """Get A/B test results."""
    try:
        test_key = f"ab_test_{test_name}"
        if test_key not in performance_monitor.metrics_store:
            raise HTTPException(status_code=404, detail="A/B test not found")
        
        test_metrics = performance_monitor.metrics_store[test_key]
        
        # Calculate test results
        variant_a = test_metrics["variant_a"]
        variant_b = test_metrics["variant_b"]
        
        results = {
            "test_name": test_name,
            "status": "running" if datetime.utcnow() < datetime.fromisoformat(test_metrics["end_time"]) else "completed",
            "variant_a": {
                "config": variant_a["config"],
                "requests": variant_a["requests"],
                "success_rate": variant_a["successes"] / variant_a["requests"] if variant_a["requests"] > 0 else 0,
                "avg_response_time": variant_a["avg_response_time"],
                "avg_user_satisfaction": sum(variant_a["user_satisfaction"]) / len(variant_a["user_satisfaction"]) if variant_a["user_satisfaction"] else 0
            },
            "variant_b": {
                "config": variant_b["config"],
                "requests": variant_b["requests"],
                "success_rate": variant_b["successes"] / variant_b["requests"] if variant_b["requests"] > 0 else 0,
                "avg_response_time": variant_b["avg_response_time"],
                "avg_user_satisfaction": sum(variant_b["user_satisfaction"]) / len(variant_b["user_satisfaction"]) if variant_b["user_satisfaction"] else 0
            }
        }
        
        # Determine winner
        if results["variant_a"]["success_rate"] > results["variant_b"]["success_rate"]:
            results["winner"] = "A"
        elif results["variant_b"]["success_rate"] > results["variant_a"]["success_rate"]:
            results["winner"] = "B"
        else:
            results["winner"] = "tie"
        
        return {
            "status": "success",
            "data": results
        }
    except Exception as e:
        logger.error(f"Error getting A/B test results: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard", response_class=HTMLResponse)
async def get_performance_dashboard():
    """Get HTML performance dashboard."""
    try:
        summary = await get_system_performance_summary()
        
        # Generate HTML dashboard
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>RAG System Performance Dashboard</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }}
                .metric-card {{ background: white; padding: 20px; margin: 10px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .metric-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
                .status-healthy {{ color: #28a745; font-weight: bold; }}
                .status-degraded {{ color: #ffc107; font-weight: bold; }}
                .status-critical {{ color: #dc3545; font-weight: bold; }}
                .recommendation {{ background: #e3f2fd; padding: 15px; margin: 10px 0; border-left: 4px solid #2196f3; border-radius: 4px; }}
                .recommendation.high {{ border-left-color: #f44336; background: #ffebee; }}
                .recommendation.medium {{ border-left-color: #ff9800; background: #fff3e0; }}
                .recommendation.low {{ border-left-color: #4caf50; background: #e8f5e8; }}
                .refresh-btn {{ background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 10px 0; }}
                .refresh-btn:hover {{ background: #0056b3; }}
            </style>
            <script>
                function refreshDashboard() {{
                    location.reload();
                }}
                
                function formatNumber(num) {{
                    return num.toFixed(2);
                }}
                
                function formatPercentage(num) {{
                    return (num * 100).toFixed(1) + '%';
                }}
            </script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🚀 RAG System Performance Dashboard</h1>
                    <p>Last updated: {summary['timestamp']}</p>
                    <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh</button>
                </div>
                
                <div class="metric-card">
                    <h2>📊 System Health</h2>
                    <div class="metric-grid">
                        <div>
                            <h3>Overall Score: <span class="status-{summary['system_health']['status']}">{summary['system_health']['overall_score']:.1f}/100</span></h3>
                            <p><strong>Status:</strong> <span class="status-{summary['system_health']['status']}">{summary['system_health']['status'].upper()}</span></p>
                        </div>
                        <div>
                            <h3>Issues Found: {len(summary['system_health']['issues'])}</h3>
                            {''.join([f'<p>• {issue}</p>' for issue in summary['system_health']['issues']])}
                        </div>
                    </div>
                </div>
                
                <div class="metric-card">
                    <h2>🔍 Vector Search Performance</h2>
                    <div class="metric-grid">
                        {_generate_vector_search_metrics_html(summary['performance_metrics'])}
                    </div>
                </div>
                
                <div class="metric-card">
                    <h2>🎯 Prerequisite Discovery Performance</h2>
                    <div class="metric-grid">
                        {_generate_prerequisite_metrics_html(summary['performance_metrics'])}
                    </div>
                </div>
                
                <div class="metric-card">
                    <h2>📚 Content Recommendation Performance</h2>
                    <div class="metric-grid">
                        {_generate_recommendation_metrics_html(summary['performance_metrics'])}
                    </div>
                </div>
                
                <div class="metric-card">
                    <h2>🎓 Remediation Success Rates</h2>
                    <div class="metric-grid">
                        {_generate_remediation_metrics_html(summary['performance_metrics'])}
                    </div>
                </div>
                
                <div class="metric-card">
                    <h2>💡 Performance Recommendations</h2>
                    {_generate_recommendations_html(summary['recommendations'])}
                </div>
                
                <div class="metric-card">
                    <h2>🗄️ Vector Database Statistics</h2>
                    <div class="metric-grid">
                        {_generate_vector_db_stats_html(summary['vector_database_stats'])}
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"Error generating performance dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _generate_vector_search_metrics_html(metrics: Dict[str, Any]) -> str:
    """Generate HTML for vector search metrics."""
    html = ""
    for key, value in metrics.items():
        if key.startswith("vector_search_"):
            index_name = key.replace("vector_search_", "")
            success_rate = (value["successful_queries"] / value["total_queries"]) * 100 if value["total_queries"] > 0 else 0
            
            html += f"""
            <div>
                <h3>Index: {index_name}</h3>
                <p><strong>Total Queries:</strong> {value['total_queries']}</p>
                <p><strong>Success Rate:</strong> {success_rate:.1f}%</p>
                <p><strong>Avg Response Time:</strong> {value['avg_response_time']:.3f}s</p>
                <p><strong>Avg Results per Query:</strong> {value['avg_results_per_query']:.1f}</p>
            </div>
            """
    return html

def _generate_prerequisite_metrics_html(metrics: Dict[str, Any]) -> str:
    """Generate HTML for prerequisite discovery metrics."""
    if "prerequisite_discovery" not in metrics:
        return "<p>No prerequisite discovery metrics available</p>"
    
    prereq_metrics = metrics["prerequisite_discovery"]
    success_rate = (prereq_metrics["successful_requests"] / prereq_metrics["total_requests"]) * 100 if prereq_metrics["total_requests"] > 0 else 0
    
    html = f"""
    <div>
        <h3>Overall Performance</h3>
        <p><strong>Total Requests:</strong> {prereq_metrics['total_requests']}</p>
        <p><strong>Success Rate:</strong> {success_rate:.1f}%</p>
        <p><strong>Avg Response Time:</strong> {prereq_metrics['avg_response_time']:.3f}s</p>
        <p><strong>Avg Prerequisites per Request:</strong> {prereq_metrics['avg_prerequisites_per_request']:.1f}</p>
    </div>
    <div>
        <h3>Source Breakdown</h3>
        {''.join([f'<p><strong>{source}:</strong> {stats["count"]} requests, {stats["avg_time"]:.3f}s avg, {stats["avg_prereqs"]:.1f} prereqs avg</p>' for source, stats in prereq_metrics['source_breakdown'].items()])}
    </div>
    """
    return html

def _generate_recommendation_metrics_html(metrics: Dict[str, Any]) -> str:
    """Generate HTML for content recommendation metrics."""
    html = ""
    for key, value in metrics.items():
        if key.startswith("content_recommendation_"):
            rec_type = key.replace("content_recommendation_", "")
            
            html += f"""
            <div>
                <h3>Type: {rec_type}</h3>
                <p><strong>Total Requests:</strong> {value['total_requests']}</p>
                <p><strong>Avg Response Time:</strong> {value['avg_response_time']:.3f}s</p>
                <p><strong>Avg Recommendations per Request:</strong> {value['avg_recommendations_per_request']:.1f}</p>
                <p><strong>Avg User Satisfaction:</strong> {value['avg_user_satisfaction']:.2f}/5.0</p>
            </div>
            """
    return html

def _generate_remediation_metrics_html(metrics: Dict[str, Any]) -> str:
    """Generate HTML for remediation success metrics."""
    html = ""
    for key, value in metrics.items():
        if key.startswith("remediation_success_"):
            gap_info = key.replace("remediation_success_", "")
            
            html += f"""
            <div>
                <h3>Gap Type: {gap_info}</h3>
                <p><strong>Total Remediations:</strong> {value['total_remediations']}</p>
                <p><strong>Success Rate:</strong> {(value['successful_remediations'] / value['total_remediations']) * 100:.1f}%</p>
                <p><strong>Avg Duration:</strong> {value['avg_duration']:.1f} hours</p>
                <p><strong>Avg Success Rate:</strong> {value['avg_success_rate']:.1%}</p>
            </div>
            """
    return html

def _generate_recommendations_html(recommendations: List[Dict[str, Any]]) -> str:
    """Generate HTML for performance recommendations."""
    if not recommendations:
        return "<p>No recommendations available</p>"
    
    html = ""
    for rec in recommendations:
        priority_class = rec.get("priority", "low")
        html += f"""
        <div class="recommendation {priority_class}">
            <h4>{rec['type'].title()} - {rec['priority'].title()} Priority</h4>
            <p><strong>Issue:</strong> {rec['issue']}</p>
            <p><strong>Recommendation:</strong> {rec['recommendation']}</p>
            <p><strong>Expected Improvement:</strong> {rec['expected_improvement']}</p>
        </div>
        """
    return html

def _generate_vector_db_stats_html(stats: Dict[str, Any]) -> str:
    """Generate HTML for vector database statistics."""
    if not stats:
        return "<p>No vector database statistics available</p>"
    
    html = ""
    for index_name, index_stats in stats.items():
        html += f"""
        <div>
            <h3>Index: {index_name}</h3>
            <p><strong>Total Vectors:</strong> {index_stats.get('total_vector_count', 'N/A')}</p>
            <p><strong>Dimension:</strong> {index_stats.get('dimension', 'N/A')}</p>
            <p><strong>Index Fullness:</strong> {index_stats.get('index_fullness', 'N/A')}</p>
        </div>
        """
    return html
