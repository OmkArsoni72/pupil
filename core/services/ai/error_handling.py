"""
Comprehensive Error Handling and Fallback System for RAG
Provides blazing fast fallbacks when Pinecone is unavailable.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable, Any
from functools import wraps
from datetime import datetime, timedelta
import time

from services.ai.pinecone_client import is_pinecone_available
from services.ai.enhanced_rag_integration import enhanced_rag

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CircuitBreaker:
    """
    Circuit breaker pattern for external service calls.
    Prevents cascading failures and provides fast fallbacks.
    """
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def can_execute(self) -> bool:
        """Check if the circuit breaker allows execution."""
        if self.state == "CLOSED":
            return True
        elif self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """Record a successful execution."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def record_failure(self):
        """Record a failed execution."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

# Global circuit breakers for different services
pinecone_circuit_breaker = CircuitBreaker(failure_threshold=3, timeout=30)
gemini_circuit_breaker = CircuitBreaker(failure_threshold=5, timeout=60)

class RetryConfig:
    """Configuration for retry logic."""
    
    def __init__(self, max_attempts: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay

async def exponential_backoff_retry(
    func: Callable,
    *args,
    retry_config: RetryConfig = None,
    **kwargs
) -> Any:
    """
    Retry function with exponential backoff for blazing fast recovery.
    """
    if retry_config is None:
        retry_config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(retry_config.max_attempts):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
            
            if attempt < retry_config.max_attempts - 1:
                delay = min(
                    retry_config.base_delay * (2 ** attempt),
                    retry_config.max_delay
                )
                await asyncio.sleep(delay)
    
    raise last_exception

def circuit_breaker_protection(circuit_breaker: CircuitBreaker):
    """
    Decorator to add circuit breaker protection to functions.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            if not circuit_breaker.can_execute():
                raise Exception(f"Circuit breaker is OPEN for {func.__name__}")
            
            try:
                result = await func(*args, **kwargs)
                circuit_breaker.record_success()
                return result
            except Exception as e:
                circuit_breaker.record_failure()
                raise e
        
        return wrapper
    return decorator

class RAGFallbackManager:
    """
    Manages fallback strategies when RAG services are unavailable.
    Provides blazing fast alternatives to maintain system performance.
    """
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        self.fallback_prerequisites = self._load_fallback_prerequisites()
    
    def _load_fallback_prerequisites(self) -> Dict[str, List[Dict[str, Any]]]:
        """Load hardcoded fallback prerequisites for common gaps."""
        return {
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
            "physics": [
                {"topic": "basic_measurements", "grade_level": "middle", "priority": 1, "description": "Units, measurements, and scientific notation"},
                {"topic": "force_and_motion", "grade_level": "middle", "priority": 2, "description": "Basic concepts of force, motion, and energy"},
                {"topic": "mathematical_foundations", "grade_level": "middle", "priority": 3, "description": "Algebra and trigonometry for physics"}
            ],
            "chemistry": [
                {"topic": "atomic_structure", "grade_level": "high", "priority": 1, "description": "Basic atomic theory and structure"},
                {"topic": "chemical_bonding", "grade_level": "high", "priority": 2, "description": "Types of chemical bonds"},
                {"topic": "stoichiometry", "grade_level": "high", "priority": 3, "description": "Chemical calculations and mole concept"}
            ]
        }
    
    async def get_cached_prerequisites(self, gap_code: str, grade_level: str) -> Optional[List[Dict[str, Any]]]:
        """Get cached prerequisites if available and not expired."""
        cache_key = f"{gap_code}_{grade_level}"
        
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                logger.info(f"Using cached prerequisites for {gap_code}")
                return cached_data
        
        return None
    
    def cache_prerequisites(self, gap_code: str, grade_level: str, prerequisites: List[Dict[str, Any]]):
        """Cache prerequisites for future use."""
        cache_key = f"{gap_code}_{grade_level}"
        self.cache[cache_key] = (prerequisites, time.time())
        logger.info(f"Cached prerequisites for {gap_code}")
    
    async def get_fallback_prerequisites(self, gap_code: str, grade_level: str) -> List[Dict[str, Any]]:
        """Get fallback prerequisites when RAG is unavailable."""
        logger.warning(f"Using fallback prerequisites for {gap_code}")
        
        # Try to find matching fallback
        gap_lower = gap_code.lower()
        for key, prereqs in self.fallback_prerequisites.items():
            if key in gap_lower:
                return prereqs
        
        # Generic fallback
        return [
            {
                "topic": "basic_concepts",
                "grade_level": "previous",
                "priority": 1,
                "description": f"Fundamental concepts needed for {gap_code}",
                "learning_objectives": [f"Understand basic principles of {gap_code}"],
                "source": "fallback"
            }
        ]

# Global fallback manager
fallback_manager = RAGFallbackManager()

class EnhancedRAGWithFallback:
    """
    Enhanced RAG integration with comprehensive fallback strategies.
    Ensures blazing fast performance even when services are down.
    """
    
    def __init__(self):
        self.pinecone_available = is_pinecone_available()
    
    @circuit_breaker_protection(pinecone_circuit_breaker)
    async def discover_prerequisites_with_fallback(
        self, 
        gap_code: str, 
        grade_level: str, 
        subject: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Discover prerequisites with comprehensive fallback strategies.
        """
        # 1. Check cache first (blazing fast)
        cached = await fallback_manager.get_cached_prerequisites(gap_code, grade_level)
        if cached:
            return cached
        
        # 2. Try enhanced RAG with retry
        if self.pinecone_available:
            try:
                prerequisites = await exponential_backoff_retry(
                    enhanced_rag.discover_prerequisites,
                    gap_code, grade_level, subject,
                    retry_config=RetryConfig(max_attempts=2, base_delay=0.5)
                )
                
                # Cache successful results
                fallback_manager.cache_prerequisites(gap_code, grade_level, prerequisites)
                return prerequisites
                
            except Exception as e:
                logger.warning(f"Enhanced RAG failed: {e}")
        
        # 3. Fallback to hardcoded prerequisites
        fallback_prereqs = await fallback_manager.get_fallback_prerequisites(gap_code, grade_level)
        
        # Cache fallback results
        fallback_manager.cache_prerequisites(gap_code, grade_level, fallback_prereqs)
        return fallback_prereqs
    
    async def get_prerequisite_learning_path_with_fallback(
        self, 
        prerequisites: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get learning path with fallback strategies.
        """
        try:
            return await enhanced_rag.get_prerequisite_learning_path(prerequisites)
        except Exception as e:
            logger.warning(f"Learning path generation failed: {e}")
            
            # Fallback learning path
            return {
                "total_prerequisites": len(prerequisites),
                "estimated_duration_hours": len(prerequisites) * 2,
                "prerequisite_sequence": sorted(prerequisites, key=lambda x: x.get("priority", 999)),
                "learning_strategy": "sequential_mastery",
                "assessment_checkpoints": [
                    {
                        "prerequisite_index": i,
                        "topic": prereq["topic"],
                        "assessment_type": "mastery_check",
                        "passing_threshold": 0.8
                    }
                    for i, prereq in enumerate(prerequisites)
                ],
                "source": "fallback"
            }

# Global instance with fallback support
rag_with_fallback = EnhancedRAGWithFallback()

# Convenience functions for backward compatibility
async def discover_prerequisites_with_fallback(
    gap_code: str, 
    grade_level: str, 
    subject: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Discover prerequisites with comprehensive fallback support."""
    return await rag_with_fallback.discover_prerequisites_with_fallback(gap_code, grade_level, subject)

async def get_prerequisite_learning_path_with_fallback(
    prerequisites: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Get learning path with fallback support."""
    return await rag_with_fallback.get_prerequisite_learning_path_with_fallback(prerequisites)
