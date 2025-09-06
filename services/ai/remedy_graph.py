import os
from typing import Dict, Any, List, Literal, Optional
from pydantic import BaseModel
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# Import Content Agent for integration
from services.ai.content_graph import build_graph as build_content_graph, CHECKPOINTER as CONTENT_CHECKPOINTER

# LLM for Remedy Agent
REMEDY_LLM = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    temperature=0.1,  # Lower temperature for more consistent classification
    google_api_key=os.environ["GEMINI_API_KEY"],
)

# Gap Types from PRD
GapType = Literal[
    "knowledge",
    "conceptual", 
    "application",
    "foundational",
    "retention",
    "engagement"
]

# Learning Modes from Content Agent
Mode = Literal[
    "learn_by_reading",
    "learn_by_writing", 
    "learn_by_watching",
    "learn_by_playing",
    "learn_by_doing",
    "learn_by_solving",
    "learn_by_questioning_debating",
    "learn_by_listening_speaking",
    "learning_by_assessment",
]

class GapEvidence(BaseModel):
    code: str
    evidence: Optional[List[str]] = None

class RemediationPlan(BaseModel):
    gap_type: GapType
    selected_modes: List[Mode]
    content_specifications: Dict[str, Any]
    priority: int = 1
    estimated_duration_minutes: int = 15

class RemedyState(BaseModel):
    # Input
    classified_gaps: List[GapEvidence]
    student_id: str
    teacher_class_id: str
    context_refs: Dict[str, Any] = {}
    
    # Processing
    gap_analysis: Dict[str, Any] = {}
    remediation_plans: List[RemediationPlan] = []
    prerequisite_discoveries: Dict[str, Any] = {}
    
    # Output
    final_plans: List[RemediationPlan] = []
    content_job_ids: List[str] = []

# Gap Type Classification Logic
GAP_TYPE_KEYWORDS = {
    "knowledge": ["basic", "fact", "term", "definition", "information", "recall", "memory"],
    "conceptual": ["concept", "principle", "theory", "understanding", "relationship", "why", "how"],
    "application": ["apply", "solve", "practice", "problem", "exercise", "implementation"],
    "foundational": ["foundation", "prerequisite", "basic", "elementary", "grade", "level", "fundamental"],
    "retention": ["forgot", "remember", "recall", "retention", "spaced", "repetition"],
    "engagement": ["motivation", "interest", "attention", "participation", "bored", "disengaged"]
}

MODE_STRATEGIES = {
    "knowledge": ["learn_by_reading", "learn_by_watching", "learning_by_assessment"],
    "conceptual": ["learn_by_questioning_debating", "learn_by_doing", "learn_by_reading"],
    "application": ["learn_by_solving", "learn_by_playing", "learn_by_doing"],
    "foundational": ["learn_by_reading", "learn_by_watching"],  # Will escalate to RAG
    "retention": ["learn_by_reading", "learn_by_solving", "learn_by_playing"],
    "engagement": ["learn_by_playing", "learn_by_listening_speaking", "learn_by_watching"]
}

async def gap_classifier_node(state: RemedyState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Use pre-classified gap types from Reports Agent or classify based on gap code and evidence.
    """
    print(f"\n🔍 [GAP_CLASSIFIER] Starting gap classification...")
    print(f"🔍 [GAP_CLASSIFIER] Processing {len(state.classified_gaps)} gaps")
    
    gap_analysis = {}
    
    for i, gap in enumerate(state.classified_gaps):
        gap_code = gap.code.lower()
        evidence = gap.evidence or []
        evidence_text = " ".join(evidence).lower()
        
        # Check if gap type is already classified
        if hasattr(gap, 'type') and gap.type:
            # Use pre-classified type from Reports Agent
            gap_type = gap.type.replace('_gap', '').lower()  # Convert "conceptual_gap" to "conceptual"
            confidence = 0.95
            reasoning = f"Using pre-classified type '{gap_type}' from Reports Agent"
            print(f"🔍 [GAP_CLASSIFIER] Gap {i+1} ({gap_code}): Using pre-classified type '{gap_type}'")
        else:
            # Fallback to keyword-based classification
            print(f"🔍 [GAP_CLASSIFIER] Gap {i+1} ({gap_code}): Classifying based on keywords...")
            
            # Score each gap type based on keywords
            scores = {}
            for gap_type, keywords in GAP_TYPE_KEYWORDS.items():
                score = 0
                # Check gap code
                for keyword in keywords:
                    if keyword in gap_code:
                        score += 2
                # Check evidence
                for keyword in keywords:
                    if keyword in evidence_text:
                        score += 1
                scores[gap_type] = score
            
            # Determine best match
            best_type = max(scores.items(), key=lambda x: x[1])
            confidence = best_type[1] / (len(GAP_TYPE_KEYWORDS[best_type[0]]) * 2 + len(evidence))
            gap_type = best_type[0]
            reasoning = f"Classified as {gap_type} based on keywords in code and evidence"
        
        gap_analysis[f"gap_{i}"] = {
            "original_gap": gap,
            "gap_type": gap_type,
            "confidence": confidence,
            "reasoning": reasoning
        }
        
        print(f"🔍 [GAP_CLASSIFIER] Gap {i}: '{gap_code}' → {gap_type} (confidence: {confidence:.2f})")
    
    print(f"✅ [GAP_CLASSIFIER] Classification completed")
    return {"gap_analysis": gap_analysis}

async def strategy_planner_node(state: RemedyState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Generate remediation plans for each classified gap.
    """
    print(f"\n📋 [STRATEGY_PLANNER] Starting strategy planning...")
    
    remediation_plans = []
    
    for gap_key, analysis in state.gap_analysis.items():
        gap_type = analysis["gap_type"]
        original_gap = analysis["original_gap"]
        
        # Get recommended modes for this gap type
        recommended_modes = MODE_STRATEGIES.get(gap_type, ["learn_by_reading", "learning_by_assessment"])
        
        # Generate content specifications based on gap type and evidence
        content_specs = await _generate_content_specifications(gap_type, original_gap, state.context_refs)
        
        plan = RemediationPlan(
            gap_type=gap_type,
            selected_modes=recommended_modes,
            content_specifications=content_specs,
            priority=1,  # Can be enhanced with priority logic
            estimated_duration_minutes=15
        )
        
        remediation_plans.append(plan)
        print(f"📋 [STRATEGY_PLANNER] Created plan for {gap_type} gap: {recommended_modes}")
    
    print(f"✅ [STRATEGY_PLANNER] Generated {len(remediation_plans)} remediation plans")
    return {"remediation_plans": remediation_plans}

async def _generate_content_specifications(gap_type: GapType, gap: GapEvidence, context_refs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate detailed content specifications for Content Agent based on gap type.
    """
    base_specs = {
        "gap_code": gap.code,
        "gap_evidence": gap.evidence or [],
        "context_refs": context_refs,
        "targeted_remediation": True
    }
    
    # Add gap-type specific specifications
    if gap_type == "knowledge":
        base_specs.update({
            "focus": "factual_information",
            "include_glossary": True,
            "include_memory_aids": True,
            "assessment_focus": "recall"
        })
    elif gap_type == "conceptual":
        base_specs.update({
            "focus": "understanding_relationships",
            "include_visualizations": True,
            "include_analogies": True,
            "assessment_focus": "analysis"
        })
    elif gap_type == "application":
        base_specs.update({
            "focus": "practical_problem_solving",
            "progressive_difficulty": True,
            "include_step_by_step": True,
            "assessment_focus": "application"
        })
    elif gap_type == "foundational":
        base_specs.update({
            "focus": "prerequisite_knowledge",
            "escalation_required": True,
            "include_basic_concepts": True,
            "assessment_focus": "foundation_check"
        })
    elif gap_type == "retention":
        base_specs.update({
            "focus": "spaced_repetition",
            "include_refreshers": True,
            "include_mnemonics": True,
            "assessment_focus": "retention_check"
        })
    elif gap_type == "engagement":
        base_specs.update({
            "focus": "motivational_content",
            "include_gamification": True,
            "include_storytelling": True,
            "assessment_focus": "engagement_check"
        })
    
    return base_specs

async def prerequisite_discovery_node(state: RemedyState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Handle RAG-based prerequisite discovery for foundational gaps.
    """
    print(f"\n🔍 [PREREQUISITE_DISCOVERY] Starting prerequisite discovery...")
    
    prerequisite_discoveries = {}
    updated_plans = []
    
    for plan in state.remediation_plans:
        if plan.gap_type == "foundational":
            print(f"🔍 [PREREQUISITE_DISCOVERY] Processing foundational gap: {plan.content_specifications['gap_code']}")
            
            # Use RAG integration for prerequisite discovery
            grade_level = state.context_refs.get('grade_level', 'unknown')
            prerequisites = await _discover_prerequisites(plan.content_specifications['gap_code'], grade_level)
            
            prerequisite_discoveries[plan.content_specifications['gap_code']] = {
                "prerequisites": prerequisites,
                "escalation_level": 1,
                "discovery_method": "rag_simulation"
            }
            
            # Update plan with prerequisite information
            plan.content_specifications["prerequisites"] = prerequisites
            plan.content_specifications["escalation_level"] = 1
            
            print(f"🔍 [PREREQUISITE_DISCOVERY] Found {len(prerequisites)} prerequisites")
        
        updated_plans.append(plan)
    
    print(f"✅ [PREREQUISITE_DISCOVERY] Completed prerequisite discovery")
    return {
        "remediation_plans": updated_plans,
        "prerequisite_discoveries": prerequisite_discoveries
    }

async def _discover_prerequisites(gap_code: str, grade_level: str = "unknown") -> List[Dict[str, Any]]:
    """
    Use RAG integration for prerequisite discovery.
    """
    from services.ai.rag_integration import discover_prerequisites
    
    try:
        prerequisites = await discover_prerequisites(gap_code, grade_level)
        return prerequisites
    except Exception as e:
        print(f"❌ [REMEDY_GRAPH] RAG discovery failed: {str(e)}")
        # Fallback to basic prerequisites
        return [
            {"topic": "basic_concepts", "grade_level": "previous", "priority": 1, "description": f"Fundamental concepts for {gap_code}"}
        ]

async def content_agent_integration_node(state: RemedyState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Pass remediation plans to Content Agent and collect job IDs.
    """
    print(f"\n🔗 [CONTENT_INTEGRATION] Starting Content Agent integration...")
    print(f"🔗 [CONTENT_INTEGRATION] Processing {len(state.remediation_plans)} plans")
    
    content_job_ids = []
    
    for i, plan in enumerate(state.remediation_plans):
        print(f"🔗 [CONTENT_INTEGRATION] Processing plan {i+1}: {plan.gap_type}")
        
        # Prepare Content Agent request
        content_request = {
            "teacher_class_id": state.teacher_class_id,
            "student_id": state.student_id,
            "duration_minutes": plan.estimated_duration_minutes,
            "modes": plan.selected_modes,
            "learning_gaps": [{"code": plan.content_specifications["gap_code"], "evidence": plan.content_specifications["gap_evidence"]}],
            "context_refs": state.context_refs,
            "options": {
                "remedy_mode": True,
                "gap_type": plan.gap_type,
                "content_specifications": plan.content_specifications
            }
        }
        
        # TODO: Actually invoke Content Agent
        # For now, simulate job creation
        job_id = f"CONTENT_JOB_{i+1}_{plan.gap_type}"
        content_job_ids.append(job_id)
        
        print(f"🔗 [CONTENT_INTEGRATION] Created content job: {job_id}")
    
    print(f"✅ [CONTENT_INTEGRATION] Created {len(content_job_ids)} content jobs")
    return {"content_job_ids": content_job_ids}

async def finalizer_node(state: RemedyState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Finalize the remedy process and prepare output.
    """
    print(f"\n✅ [FINALIZER] Finalizing remedy process...")
    
    # Prepare final output
    final_plans = state.remediation_plans
    
    print(f"✅ [FINALIZER] Finalized {len(final_plans)} remediation plans")
    print(f"✅ [FINALIZER] Created {len(state.content_job_ids)} content jobs")
    
    return {
        "final_plans": final_plans,
        "status": "completed",
        "summary": {
            "total_gaps": len(state.classified_gaps),
            "total_plans": len(final_plans),
            "gap_types": list(set(plan.gap_type for plan in final_plans)),
            "content_jobs": len(state.content_job_ids)
        }
    }

def build_remedy_graph() -> StateGraph:
    """
    Build the Remedy Agent graph.
    """
    print(f"\n🏗️ [REMEDY_GRAPH] Building Remedy Agent graph...")
    
    graph = StateGraph(RemedyState)
    
    # Add nodes
    graph.add_node("gap_classifier", gap_classifier_node)
    graph.add_node("strategy_planner", strategy_planner_node)
    graph.add_node("prerequisite_discovery", prerequisite_discovery_node)
    graph.add_node("content_integration", content_agent_integration_node)
    graph.add_node("finalizer", finalizer_node)
    
    # Define flow
    graph.set_entry_point("gap_classifier")
    graph.add_edge("gap_classifier", "strategy_planner")
    graph.add_edge("strategy_planner", "prerequisite_discovery")
    graph.add_edge("prerequisite_discovery", "content_integration")
    graph.add_edge("content_integration", "finalizer")
    graph.add_edge("finalizer", END)
    
    print(f"✅ [REMEDY_GRAPH] Remedy Agent graph built successfully")
    return graph

# Public checkpointer for Remedy Agent
REMEDY_CHECKPOINTER = MemorySaver()
