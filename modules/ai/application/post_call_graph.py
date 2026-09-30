"""Post-call processing graph."""

from __future__ import annotations

import logging
from typing import Any, Literal, TypedDict

# Placeholder for LangGraph imports until added to dependencies
# from langgraph.graph import StateGraph, START, END
# from langgraph.checkpoint.postgres import PostgresSaver

logger = logging.getLogger(__name__)


class PostCallState(TypedDict):
    """State for the post-call graph."""

    call_id: str
    tenant_id: str
    transcript: str
    outcome: str | None
    extracted_data: dict[str, Any]
    requires_review: bool
    email_draft_id: str | None
    crm_synced: bool


async def extract_outcome(state: PostCallState) -> dict[str, Any]:
    """Node: Extract structured data from transcript."""
    logger.info(f"Extracting outcome for call {state['call_id']}")

    # In reality, calls AIGateway
    # Mocking extraction
    extracted = {"outcome": "MEETING_BOOKED", "objections": ["Price"], "next_steps": "Send calendar invite"}

    # Force review if confidence is low or specific outcome
    requires_review = extracted["outcome"] == "NEEDS_REVIEW"

    return {"outcome": extracted["outcome"], "extracted_data": extracted, "requires_review": requires_review}


async def sync_crm(state: PostCallState) -> dict[str, Any]:
    """Node: Sync outcomes to CRM."""
    logger.info(f"Syncing CRM for call {state['call_id']}")
    return {"crm_synced": True}


async def draft_email(state: PostCallState) -> dict[str, Any]:
    """Node: Draft follow-up email."""
    logger.info(f"Drafting email for call {state['call_id']}")
    return {"email_draft_id": "draft_123"}


def should_review(state: PostCallState) -> Literal["human_review", "sync_crm"]:
    """Conditional edge: check if human review is needed."""
    if state.get("requires_review"):
        return "human_review"
    return "sync_crm"


# MVP Graph Definition (Mocked until langgraph is installed)
class MockStateGraph:
    def __init__(self, state_schema):
        self.nodes = {}
        self.edges = []

    def add_node(self, name, func):
        self.nodes[name] = func

    def add_edge(self, start, end):
        self.edges.append((start, end))

    def add_conditional_edges(self, start, condition, path_map):
        pass

    def compile(self, checkpointer=None):
        return self


def build_post_call_graph():
    """Build the LangGraph state machine for post-call processing."""
    graph = MockStateGraph(PostCallState)

    graph.add_node("extract_outcome", extract_outcome)
    graph.add_node("human_review", lambda s: s)  # Passthrough for interrupt
    graph.add_node("sync_crm", sync_crm)
    graph.add_node("draft_email", draft_email)

    graph.add_edge("START", "extract_outcome")
    graph.add_conditional_edges(
        "extract_outcome", should_review, {"human_review": "human_review", "sync_crm": "sync_crm"}
    )

    graph.add_edge("human_review", "sync_crm")
    graph.add_edge("sync_crm", "draft_email")
    graph.add_edge("draft_email", "END")

    # In production:
    # memory = PostgresSaver(conn)
    # return graph.compile(checkpointer=memory, interrupt_before=["human_review"])

    return graph.compile()
