from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any
from app.tools.rule_engine import get_db_connection, get_rule_with_precedence

class GetProfileInput(BaseModel):
    student_id: str = Field(description="The ID of the student")

def get_profile(input_data: GetProfileInput) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM student WHERE student_id = ?", (input_data.student_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return {"error": f"Student {input_data.student_id} not found."}
    return {"student": dict(row), "citation": None}

class GetAttendanceInput(BaseModel):
    student_id: str = Field(description="The ID of the student")
    course_code: str = Field(default="all", description="Specific course code or 'all'")

def get_attendance(input_data: GetAttendanceInput) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    if input_data.course_code.lower() == "all":
        cursor.execute("SELECT * FROM attendance WHERE student_id = ?", (input_data.student_id,))
    else:
        cursor.execute("SELECT * FROM attendance WHERE student_id = ? AND course_code = ?", (input_data.student_id, input_data.course_code))
    rows = cursor.fetchall()
    conn.close()
    return {"attendance": [dict(r) for r in rows], "citation": None}

class GetResultsInput(BaseModel):
    student_id: str = Field(description="The ID of the student")

def get_results(input_data: GetResultsInput) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM results WHERE student_id = ?", (input_data.student_id,))
    rows = cursor.fetchall()
    conn.close()
    return {"results": [dict(r) for r in rows], "citation": None}

class GetCgpaBacklogsInput(BaseModel):
    student_id: str = Field(description="The ID of the student")

def get_cgpa_backlogs(input_data: GetCgpaBacklogsInput) -> Dict[str, Any]:
    conn = get_db_connection()
    cursor = conn.cursor()
    # Simplified logic for CGPA and Backlogs
    cursor.execute("SELECT * FROM results WHERE student_id = ?", (input_data.student_id,))
    rows = cursor.fetchall()
    conn.close()
    
    total_credits = 0
    earned_points = 0
    backlogs = []
    
    for r in rows:
        # Assuming courses table has credits, let's fetch it or just mock for now
        # Actually, need to join with courses to get credits
        pass
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.course_code, r.result, c.credits 
        FROM results r
        JOIN courses c ON r.course_code = c.course_code
        WHERE r.student_id = ?
    """, (input_data.student_id,))
    data = cursor.fetchall()
    conn.close()
    
    for d in data:
        if d['result'] == 'PASS':
            total_credits += d['credits']
            # Assume 10 points for PASS for simplicity
            earned_points += 10 * d['credits']
        elif d['result'] in ['FAIL', 'ABSENT', 'DETAINED']:
            backlogs.append(d['course_code'])
            
    cgpa = (earned_points / total_credits) if total_credits > 0 else 0.0
    return {"cgpa": round(cgpa, 2), "backlogs": list(set(backlogs)), "citation": None}

class CheckExamEligibilityInput(BaseModel):
    student_id: str = Field(description="The ID of the student")
    course_code: str = Field(description="The course code to check")
    as_of_date: Optional[str] = Field(default=None, description="Current date")

def check_exam_eligibility(input_data: CheckExamEligibilityInput) -> Dict[str, Any]:
    prof = get_profile(GetProfileInput(student_id=input_data.student_id))
    if "error" in prof:
        return prof
    student = prof['student']
    
    att = get_attendance(GetAttendanceInput(student_id=input_data.student_id, course_code=input_data.course_code))
    if not att['attendance']:
        return {"error": "Attendance record not found"}
        
    record = att['attendance'][0]
    percent = (record['classes_attended'] / record['classes_held']) * 100 if record['classes_held'] > 0 else 0
    
    rule = get_rule_with_precedence('ATTENDANCE_MIN', input_data.as_of_date, student['programme'], student['batch'])
    condonable_rule = get_rule_with_precedence('ATTENDANCE_CONDONATION', input_data.as_of_date, student['programme'], student['batch'])
    
    threshold = float(rule['value']) if rule else 75.0
    condonable_threshold = float(condonable_rule['value']) if condonable_rule else 65.0
    
    status = "NOT_ELIGIBLE"
    classes_needed = 0
    
    if percent >= threshold:
        status = "ELIGIBLE"
    elif percent >= condonable_threshold:
        status = "CONDONABLE"
    
    if percent < threshold:
        classes_needed = max(0, int((threshold/100.0 * record['classes_held']) - record['classes_attended']))
        
    return {
        "status": status,
        "rule_id": rule['rule_id'] if rule else None,
        "threshold": threshold,
        "classes_needed": classes_needed,
        "citation": f"Rule {rule['rule_id']} from Doc {rule['source_doc_id']}" if rule else "Fallback 75%"
    }

class CheckSupplementaryEligibilityInput(BaseModel):
    student_id: str = Field(description="The ID of the student")
    as_of_date: Optional[str] = Field(default=None)

def check_supplementary_eligibility(input_data: CheckSupplementaryEligibilityInput) -> Dict[str, Any]:
    prof = get_profile(GetProfileInput(student_id=input_data.student_id))
    if "error" in prof:
        return prof
    student = prof['student']
    
    rule = get_rule_with_precedence('SUPPLEMENTARY_ELIGIBILITY', input_data.as_of_date, student['programme'], student['batch'])
    
    cg_backlogs = get_cgpa_backlogs(GetCgpaBacklogsInput(student_id=input_data.student_id))
    backlogs = cg_backlogs.get('backlogs', [])
    
    # Example parameter parse (if rule value is 'FAIL_COUNT <= 2')
    # Since we are not doing LLM arithmetic here, we'll parse it simply or just assume threshold
    threshold = 2
    if rule and rule['operator'] == '<=':
        threshold = int(rule['value'])
        
    if len(backlogs) <= threshold:
        status = "ELIGIBLE"
    else:
        status = "NOT_ELIGIBLE"
        
    return {
        "status": status,
        "rule_id": rule['rule_id'] if rule else None,
        "backlog_count": len(backlogs),
        "threshold": threshold,
        "citation": f"Rule {rule['rule_id']} from Doc {rule['source_doc_id']}" if rule else "Default threshold 2"
    }

class CheckPlacementEligibilityInput(BaseModel):
    student_id: str = Field(description="The ID of the student")
    as_of_date: Optional[str] = Field(default=None)

def check_placement_eligibility(input_data: CheckPlacementEligibilityInput) -> Dict[str, Any]:
    prof = get_profile(GetProfileInput(student_id=input_data.student_id))
    if "error" in prof:
        return prof
    student = prof['student']
    
    rule = get_rule_with_precedence('PLACEMENT_ELIGIBILITY', input_data.as_of_date, student['programme'], student['batch'])
    
    cg_backlogs = get_cgpa_backlogs(GetCgpaBacklogsInput(student_id=input_data.student_id))
    cgpa = cg_backlogs.get('cgpa', 0)
    backlogs = cg_backlogs.get('backlogs', [])
    
    threshold = 6.0
    if rule and rule['operator'] == '>=':
        threshold = float(rule['value'])
        
    if cgpa >= threshold and len(backlogs) == 0:
        status = "ELIGIBLE"
    else:
        status = "NOT_ELIGIBLE"
        
    return {
        "status": status,
        "rule_id": rule['rule_id'] if rule else None,
        "cgpa": cgpa,
        "backlogs": len(backlogs),
        "threshold": threshold,
        "citation": f"Rule {rule['rule_id']} from Doc {rule['source_doc_id']}" if rule else f"Default CGPA threshold {threshold}"
    }

class SimulateWhatIfInput(BaseModel):
    student_id: str = Field(description="The ID of the student")
    course_code: str = Field(description="The course to simulate")
    target_attendance: float = Field(description="Target attendance % to achieve")

def simulate_what_if(input_data: SimulateWhatIfInput) -> Dict[str, Any]:
    att = get_attendance(GetAttendanceInput(student_id=input_data.student_id, course_code=input_data.course_code))
    if not att['attendance']:
        return {"error": "Attendance record not found"}
        
    record = att['attendance'][0]
    held = record['classes_held']
    attended = record['classes_attended']
    
    target_frac = input_data.target_attendance / 100.0
    # Equation: (attended + x) / (held + x) = target_frac
    # attended + x = target_frac * held + target_frac * x
    # x - target_frac * x = target_frac * held - attended
    # x * (1 - target_frac) = target_frac * held - attended
    
    if input_data.target_attendance >= 100:
        return {"error": "Cannot target 100% or above."}
        
    x = (target_frac * held - attended) / (1 - target_frac)
    classes_to_attend = max(0, int(x + 0.999)) # ceil
    
    return {
        "assumptions": [
            f"You will attend every future class for {input_data.course_code}",
            f"The classes held will increase by exactly {classes_to_attend}"
        ],
        "classes_to_attend": classes_to_attend,
        "citation": None
    }

class GetRuleInput(BaseModel):
    rule_id: str = Field(description="The ID of the rule")
    as_of_date: Optional[str] = Field(default=None)

def get_rule(input_data: GetRuleInput) -> Dict[str, Any]:
    rule = get_rule_with_precedence(input_data.rule_id, input_data.as_of_date)
    if not rule:
        return {"error": f"Rule {input_data.rule_id} not found or not applicable."}
    return {
        "rule": rule,
        "citation": f"Rule {rule['rule_id']} from Doc {rule['source_doc_id']}"
    }

TOOLS = [
    get_profile,
    get_attendance,
    get_results,
    get_cgpa_backlogs,
    check_exam_eligibility,
    check_supplementary_eligibility,
    check_placement_eligibility,
    simulate_what_if,
    get_rule
]
