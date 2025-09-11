"""
RAG Integration for Remedy Agent
Handles prerequisite discovery for foundational gaps.
"""

from typing import Dict, Any, List, Optional
import os
from pydantic import BaseModel
from langchain_google_genai import ChatGoogleGenerativeAI
from services.db_operations.base import prerequisite_cache_collection
import anyio

# LLM for RAG operations
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

async def discover_prerequisites(gap_code: str, grade_level: str, subject: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Discover prerequisite topics for a foundational gap using RAG.
    
    Args:
        gap_code: The learning gap code
        grade_level: Current grade level
        subject: Subject area (optional)
    
    Returns:
        List of prerequisite topics with metadata
    """
    print(f"🔍 [RAG] Discovering prerequisites for gap: {gap_code}")
    
    # Check cache first
    try:
        def _find_cache():
            return prerequisite_cache_collection.find_one({"gap_code": gap_code, "grade_level": grade_level, "subject": subject})
        cached = await anyio.to_thread.run_sync(_find_cache)
        if cached and isinstance(cached.get("prerequisites"), list) and cached.get("prerequisites"):
            print(f"🔍 [RAG] Using cached prerequisites for {gap_code}")
            return cached["prerequisites"]
    except Exception as _e:
        print(f"⚠️ [RAG] Cache lookup failed: {_e}")

    # Build RAG query
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
        # Query RAG system (simulated for now)
        response = await RAG_LLM.ainvoke(query)
        
        # Parse response into structured prerequisites
        prerequisites = _parse_rag_response(response.content, gap_code)
        
        print(f"🔍 [RAG] Found {len(prerequisites)} prerequisites")
        # Persist to cache
        try:
            def _upsert():
                return prerequisite_cache_collection.update_one(
                    {"gap_code": gap_code, "grade_level": grade_level, "subject": subject},
                    {"$set": {"gap_code": gap_code, "grade_level": grade_level, "subject": subject, "prerequisites": prerequisites}},
                    upsert=True,
                )
            await anyio.to_thread.run_sync(_upsert)
        except Exception as ce:
            print(f"⚠️ [RAG] Failed to cache prerequisites: {ce}")
        return prerequisites
        
    except Exception as e:
        print(f"❌ [RAG] Error in prerequisite discovery: {str(e)}")
        # Return fallback prerequisites
        fall = _get_fallback_prerequisites(gap_code, grade_level)
        # Try to cache fallback as well to avoid repeated calls
        try:
            def _upsert_f():
                return prerequisite_cache_collection.update_one(
                    {"gap_code": gap_code, "grade_level": grade_level, "subject": subject},
                    {"$set": {"gap_code": gap_code, "grade_level": grade_level, "subject": subject, "prerequisites": fall}},
                    upsert=True,
                )
            await anyio.to_thread.run_sync(_upsert_f)
        except Exception as ce:
            print(f"⚠️ [RAG] Failed to cache fallback prerequisites: {ce}")
        return fall

def _parse_rag_response(response_text: str, gap_code: str) -> List[Dict[str, Any]]:
    """
    Parse RAG response into structured prerequisite data.
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
        prerequisites = _get_fallback_prerequisites(gap_code, "unknown")
    
    return prerequisites

def _get_fallback_prerequisites(gap_code: str, grade_level: str) -> List[Dict[str, Any]]:
    """
    Provide fallback prerequisites when RAG fails.
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

async def get_prerequisite_learning_path(prerequisites: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate a learning path for prerequisite topics.
    """
    print(f"🗺️ [RAG] Generating learning path for {len(prerequisites)} prerequisites")
    
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

# TODO: Integrate with actual RAG system
# This would typically involve:
# 1. Vector database queries for similar gaps
# 2. Curriculum mapping to find prerequisite topics
# 3. Learning objective extraction
# 4. Difficulty progression analysis
