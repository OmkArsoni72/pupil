import os
from typing import Dict, Any, List, Literal

from pydantic import BaseModel

# LangGraph / LangChain
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.runnables import RunnableConfig
from langchain_google_genai import ChatGoogleGenerativeAI

# Import nodes from separate files
from core.services.ai.helper.orchestrator_node import orchestrator_node
from core.services.ai.helper.reading_node import node_learn_by_reading
from core.services.ai.helper.writing_node import node_learn_by_writing
from core.services.ai.helper.watching_node import node_learn_by_watching
from core.services.ai.helper.playing_node import node_learn_by_playing
from core.services.ai.helper.doing_node import node_learn_by_doing
from core.services.ai.helper.solving_node import node_learn_by_solving
from core.services.ai.helper.debating_node import node_learn_by_questioning_debating
from core.services.ai.helper.listening_speaking_node import node_learn_by_listening_speaking
from core.services.ai.helper.assessment_node import node_learning_by_assessment
from core.services.ai.helper.collector_node import collector_node

from core.services.ai.schemas import (
    LearnByReadingPayload,
    LearnByWritingPayload,
    LearnByDoingPayload,
    LearnByListeningSpeakingPayload,
)


# --------------- Shared Types ---------------
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


class State(BaseModel):
    # immutable inputs
    route: Literal["AHS", "REMEDY"]
    req: Dict[str, Any]
    # orchestration
    selected_modes: List[Mode] = []
    diagnostics: Dict[str, Any] = {}
    dependencies_ok: bool = True
    # output handles
    db_handles: Dict[str, str] = {}      # where artifacts are stored (session/remedy ids)


# --------- LLM (provider/model can be swapped) ---------
LLM = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.2,
    google_api_key=os.environ["GEMINI_API_KEY"],
)


# ---------------- Build Graph ----------------
def build_graph(active_modes: List[Mode]) -> StateGraph:
    """
    Builds the LangGraph workflow for content generation.
    """
    print(f"\n🏗️ [GRAPH] Building graph with active modes: {active_modes}")
    
    g = StateGraph(State)
    g.add_node("orchestrator", orchestrator_node)
    g.add_node("collector", collector_node)

    # feature nodes
    nodes = {
        "learn_by_reading": node_learn_by_reading,
        "learn_by_writing": node_learn_by_writing,
        "learn_by_watching": node_learn_by_watching,
        "learn_by_playing": node_learn_by_playing,
        "learn_by_doing": node_learn_by_doing,
        "learn_by_solving": node_learn_by_solving,
        "learn_by_questioning_debating": node_learn_by_questioning_debating,
        "learn_by_listening_speaking": node_learn_by_listening_speaking,
        "learning_by_assessment": node_learning_by_assessment,
    }
    
    print(f"🏗️ [GRAPH] Adding {len(nodes)} feature nodes to graph")
    for name, fn in nodes.items():
        g.add_node(name, fn)
        print(f"🏗️ [GRAPH] Added node: {name}")

    # edges
    g.set_entry_point("orchestrator")
    print(f"🏗️ [GRAPH] Set orchestrator as entry point")
    
    # Fan-out from orchestrator to core content modes (excluding assessment)
    core_modes = [m for m in active_modes if m != "learning_by_assessment"]
    for m in core_modes:
        g.add_edge("orchestrator", m)
        print(f"🏗️ [GRAPH] Added edge: orchestrator -> {m}")
    
    # Core content nodes converge to collector
    g.add_edge("learn_by_reading", "collector")
    g.add_edge("learn_by_writing", "collector")
    g.add_edge("learn_by_watching", "collector")
    g.add_edge("learn_by_playing", "collector")
    g.add_edge("learn_by_doing", "collector")
    g.add_edge("learn_by_solving", "collector")
    g.add_edge("learn_by_questioning_debating", "collector")
    g.add_edge("learn_by_listening_speaking", "collector")
    
    # Assessment runs after core content (if requested)
    if "learning_by_assessment" in active_modes:
        # Assessment depends on core content for context
        g.add_edge("learn_by_reading", "learning_by_assessment")
        g.add_edge("learn_by_solving", "learning_by_assessment")
        g.add_edge("learn_by_writing", "learning_by_assessment")
        # Assessment then goes to collector
        g.add_edge("learning_by_assessment", "collector")
        print(f"🏗️ [GRAPH] Added assessment dependency edges")
    else:
        print(f"🏗️ [GRAPH] Assessment not requested, skipping dependency edges")
    
    print(f"🏗️ [GRAPH] Added all collector edges")
    
    # All nodes converge to collector, then END
    g.add_edge("collector", END)
    print(f"🏗️ [GRAPH] Added collector -> END edge")
    print(f"🏗️ [GRAPH] Graph construction completed")

    return g


# Public checkpointer (swap with Redis/DB for resilience)
CHECKPOINTER = MemorySaver()


