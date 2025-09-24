"""
Assessment Graph - LangGraph StateGraph for assessment generation.
Refactored from services/ai/assessment_generator.py
"""

from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from nodes.common_nodes.schema_node import schema_node
from nodes.common_nodes.context_node import context_node
from nodes.common_nodes.question_generation_node import question_generation_node
from nodes.assessment_nodes.assessment_node import assessment_node


class AssessmentState(TypedDict, total=False):
    # inputs
    target_exam: str
    exam_type: str
    previous_topics: list
    learning_gaps: list
    difficulty: str
    subject: str
    class_: str
    teacher_id: str
    self_assessment_mode: str
    file_url: str
    llm_model: str
    job_id: str
    # intermediate / outputs
    schema: dict
    context: dict
    questions: list
    assessment_json: dict


def build_assessment_graph() -> StateGraph:
    """Build the assessment generation graph."""
    graph = StateGraph(AssessmentState)
    
    # Add nodes
    graph.add_node("schema", schema_node)
    graph.add_node("context", context_node)
    graph.add_node("generate_questions", question_generation_node)
    graph.add_node("assessment", assessment_node)
    
    # Add edges
    graph.add_edge(START, "schema")
    graph.add_edge(START, "context")
    graph.add_edge("schema", "generate_questions")
    graph.add_edge("context", "generate_questions")
    graph.add_edge("generate_questions", "assessment")
    graph.add_edge("assessment", END)
    
    return graph.compile()
