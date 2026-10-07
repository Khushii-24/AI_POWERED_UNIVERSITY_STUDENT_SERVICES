from langgraph.graph import StateGraph, END
from app.workflow.state import WorkflowState
from app.workflow.nodes import (
    guard_node,
    classify_node,
    select_tools_node,
    retrieve_precedence_node,
    execute_tools_node,
    synthesize_node,
    verify_node,
    finalize_audit_node
)

def should_continue_after_guard(state: WorkflowState) -> str:
    if not state.get('is_safe', True):
        return "finalize"
    return "classify"

def should_continue_after_classify(state: WorkflowState) -> str:
    if state.get('clarification_needed'):
        return "finalize"
    return "select_tools"

def build_workflow() -> StateGraph:
    workflow = StateGraph(WorkflowState)
    
    # Add nodes
    workflow.add_node("guard", guard_node)
    workflow.add_node("classify", classify_node)
    workflow.add_node("select_tools", select_tools_node)
    workflow.add_node("retrieve_precedence", retrieve_precedence_node)
    workflow.add_node("execute_tools", execute_tools_node)
    workflow.add_node("synthesize", synthesize_node)
    workflow.add_node("verify", verify_node)
    workflow.add_node("finalize", finalize_audit_node)
    
    # Add edges
    workflow.set_entry_point("guard")
    
    workflow.add_conditional_edges(
        "guard",
        should_continue_after_guard,
        {
            "classify": "classify",
            "finalize": "finalize"
        }
    )
    
    workflow.add_conditional_edges(
        "classify",
        should_continue_after_classify,
        {
            "select_tools": "select_tools",
            "finalize": "finalize"
        }
    )
    
    workflow.add_edge("select_tools", "retrieve_precedence")
    workflow.add_edge("retrieve_precedence", "execute_tools")
    workflow.add_edge("execute_tools", "synthesize")
    workflow.add_edge("synthesize", "verify")
    workflow.add_edge("verify", "finalize")
    workflow.add_edge("finalize", END)
    
    return workflow.compile()
