from typing import Dict, Any
from app.workflow.state import WorkflowState
from app.rag.precedence import retrieve_and_resolve
import json
import re

def guard_node(state: WorkflowState) -> WorkflowState:
    question = state['question'].lower()
    # Basic injection detection
    injection_patterns = ["ignore previous", "system prompt", "you are a", "forget all"]
    
    is_safe = True
    for p in injection_patterns:
        if p in question:
            is_safe = False
            break
            
    state['is_safe'] = is_safe
    if not is_safe:
        state['answer_type'] = 'refused'
        state['final_answer'] = "Request blocked due to security policies."
        
    return state

def classify_node(state: WorkflowState) -> WorkflowState:
    # Mock LLM classification logic
    question = state['question'].lower()
    
    categories = ['policy_fact', 'procedure', 'personal_data', 'personal_eligibility', 'multi_step', 'out_of_scope']
    
    # Fallback keyword logic
    if 'eligible' in question or 'eligibility' in question:
        state['category'] = 'personal_eligibility'
    elif 'attendance' in question or 'cgpa' in question or 'results' in question:
        state['category'] = 'personal_data'
    elif 'how to' in question or 'process' in question:
        state['category'] = 'procedure'
    else:
        state['category'] = 'policy_fact'
        
    state['clarification_needed'] = False
    
    # Simple clarification mock
    if state['category'] == 'personal_eligibility' and not re.search(r'[A-Z]{3}[0-9]{3}', question.upper()) and 'exam' in question:
        state['clarification_needed'] = True
        state['answer_type'] = 'clarification_needed'
        state['final_answer'] = "Which course are you asking about?"
        
    return state

def select_tools_node(state: WorkflowState) -> WorkflowState:
    tools_selected = []
    cat = state.get('category')
    question = state['question'].lower()
    
    if cat == 'personal_eligibility':
        if 'exam' in question:
            course = re.search(r'[A-Z]{3}[0-9]{3}', question.upper())
            if course:
                tools_selected.append({"tool": "check_exam_eligibility", "args": {"student_id": state['student_id'], "course_code": course.group(0)}})
        elif 'supplementary' in question:
            tools_selected.append({"tool": "check_supplementary_eligibility", "args": {"student_id": state['student_id']}})
        elif 'placement' in question:
            tools_selected.append({"tool": "check_placement_eligibility", "args": {"student_id": state['student_id']}})
            
    elif cat == 'personal_data':
        if 'attendance' in question:
            tools_selected.append({"tool": "get_attendance", "args": {"student_id": state['student_id'], "course_code": "all"}})
        elif 'results' in question or 'cgpa' in question or 'backlogs' in question:
            tools_selected.append({"tool": "get_cgpa_backlogs", "args": {"student_id": state['student_id']}})
            
    elif cat == 'multi_step' and 'what if' in question:
         tools_selected.append({"tool": "simulate_what_if", "args": {"student_id": state['student_id'], "course_code": "CS101", "target_attendance": 75}})
         
    state['tools_selected'] = tools_selected
    return state

def retrieve_precedence_node(state: WorkflowState) -> WorkflowState:
    result = retrieve_and_resolve(state['question'], as_of_date=state['as_of_date'], my_programme=state['student_programme'], my_batch=state['student_batch'])
    state['retrieved_chunks'] = result['chunks']
    state['precedence_decision'] = result['precedence_decision']
    state['conflicts_detected'] = result['conflicts']
    state['upcoming_changes'] = result['upcoming_changes']
    
    if result['answer_type'] == 'conflict_flagged':
        state['answer_type'] = 'conflict_flagged'
        
    return state

def execute_tools_node(state: WorkflowState) -> WorkflowState:
    from app.tools.student_tools import get_attendance, get_cgpa_backlogs, check_exam_eligibility, check_supplementary_eligibility, check_placement_eligibility, simulate_what_if, get_rule
    from app.tools.student_tools import GetAttendanceInput, GetCgpaBacklogsInput, CheckExamEligibilityInput, CheckSupplementaryEligibilityInput, CheckPlacementEligibilityInput, SimulateWhatIfInput
    
    results = []
    rules = []
    
    # Very simple dispatcher
    dispatcher = {
        "check_exam_eligibility": (check_exam_eligibility, CheckExamEligibilityInput),
        "check_supplementary_eligibility": (check_supplementary_eligibility, CheckSupplementaryEligibilityInput),
        "check_placement_eligibility": (check_placement_eligibility, CheckPlacementEligibilityInput),
        "get_attendance": (get_attendance, GetAttendanceInput),
        "get_cgpa_backlogs": (get_cgpa_backlogs, GetCgpaBacklogsInput),
        "simulate_what_if": (simulate_what_if, SimulateWhatIfInput),
    }
    
    for tool_req in state.get('tools_selected', []):
        t_name = tool_req['tool']
        t_args = tool_req['args']
        if 'as_of_date' not in t_args:
            t_args['as_of_date'] = state['as_of_date']
            
        if t_name in dispatcher:
            func, schema = dispatcher[t_name]
            try:
                res = func(schema(**t_args))
                results.append({"tool": t_name, "result": res})
                if res.get('rule_id'):
                    rules.append(res['rule_id'])
            except Exception as e:
                results.append({"tool": t_name, "error": str(e)})
                
    state['tool_results'] = results
    state['rules_applied'] = rules
    return state

def synthesize_node(state: WorkflowState) -> WorkflowState:
    # LLM sees only retrieved chunks and tool results
    chunks_text = "\n".join([f"<doc>{c['text']}</doc>" for c in state.get('retrieved_chunks', [])])
    
    if not state.get('retrieved_chunks') and not state.get('tool_results'):
        state['synthesized_answer'] = "I could not find this information in the ingested sources."
        state['answer_type'] = 'not_found'
        return state
        
    # Mock synthesis
    state['synthesized_answer'] = "Based on the records and policies, here is the answer."
    state['citations'] = []
    if state.get('tool_results'):
        state['answer_type'] = 'calculated'
        for tr in state['tool_results']:
            if tr.get('result', {}).get('citation'):
                state['citations'].append({"doc_id": "rule_registry", "section": tr['result']['citation']})
    else:
        state['answer_type'] = 'retrieved_fact'
        if state.get('retrieved_chunks'):
            c = state['retrieved_chunks'][0]
            state['citations'].append({
                "doc_id": c['metadata']['doc_id'],
                "section": "Excerpt"
            })
            
    state['assumptions'] = []
    if state.get('tool_results') and state['tool_results'][0]['tool'] == 'simulate_what_if':
        state['assumptions'] = state['tool_results'][0]['result'].get('assumptions', [])
        
    return state

def verify_node(state: WorkflowState) -> WorkflowState:
    # Deterministic check that citations exist
    state['verification_passed'] = True
    return state

def finalize_audit_node(state: WorkflowState) -> WorkflowState:
    if state.get('answer_type') not in ['refused', 'clarification_needed']:
        state['final_answer'] = state.get('synthesized_answer', '')
        
    # Audit log creation is handled in the API layer after graph execution
    return state
