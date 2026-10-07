from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime

class WorkflowState(TypedDict):
    # Input
    trace_id: str
    question: str
    as_of_date: str
    student_id: Optional[str]
    student_programme: Optional[str]
    student_batch: Optional[str]
    
    # Process
    is_safe: bool
    category: Optional[str]
    clarification_needed: bool
    tools_selected: List[Dict[str, Any]]
    retrieved_chunks: List[Dict[str, Any]]
    precedence_decision: str
    upcoming_changes: List[Dict[str, Any]]
    conflicts_detected: List[str]
    
    # Tool Execution
    tool_results: List[Dict[str, Any]]
    rules_applied: List[str]
    
    # Synthesis & Verification
    synthesized_answer: str
    assumptions: List[str]
    citations: List[Dict[str, Any]]
    answer_type: str # retrieved_fact | calculated | not_found | clarification_needed | refused | conflict_flagged
    verification_passed: bool
    
    # Final Output
    final_answer: str
    explanation: str
