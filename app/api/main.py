from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
import time
import sqlite3

from app.workflow.graph import build_workflow
from app.db.audit import log_audit, get_audit
from app.api.ingest import router as ingest_router

app = FastAPI(title="University AI Assistant API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)

workflow = build_workflow()

class AskRequest(BaseModel):
    question: str = Field(..., description="The user's question")
    as_of_date: Optional[str] = Field(default=None, description="Current date in YYYY-MM-DD format")

class AskResponse(BaseModel):
    trace_id: str
    answer: str
    answer_type: str
    citations: List[Dict[str, Any]]
    tools_invoked: List[str]
    rules_applied: List[str]
    conflicts_detected: List[str]
    explanation: str
    as_of_date: str

@app.post("/ask", response_model=AskResponse)
async def ask_question(
    req: AskRequest,
    student_id: Optional[str] = Header(None, description="Optional identity from config/header, never from message text")
):
    start_time = time.time()
    trace_id = str(uuid.uuid4())
    as_of = req.as_of_date or datetime.now().strftime("%Y-%m-%d")
    
    # Initialize state
    state = {
        "trace_id": trace_id,
        "question": req.question,
        "as_of_date": as_of,
        "student_id": student_id,
        "student_programme": None, # Could fetch from DB if student_id is present
        "student_batch": None,
    }
    
    # Execute workflow
    result = workflow.invoke(state)
    
    # Audit log
    log_audit(trace_id, {
        "category": result.get("category"),
        "sources_retrieved": [{"doc_id": c["metadata"]["doc_id"], "score": 1.0} for c in result.get("retrieved_chunks", [])],
        "precedence_decision": result.get("precedence_decision"),
        "tools_invoked": [{"tool": t["tool"], "status": "ok"} for t in result.get("tools_selected", [])],
        "rules_applied": result.get("rules_applied", []),
        "conflicts": result.get("conflicts_detected", []),
        "answer_type": result.get("answer_type", "unknown"),
        "latency_ms": int((time.time() - start_time) * 1000)
    })
    
    return AskResponse(
        trace_id=trace_id,
        answer=result.get("final_answer", ""),
        answer_type=result.get("answer_type", "unknown"),
        citations=result.get("citations", []),
        tools_invoked=[t["tool"] for t in result.get("tools_selected", [])],
        rules_applied=result.get("rules_applied", []),
        conflicts_detected=result.get("conflicts_detected", []),
        explanation="Workflow completed.",
        as_of_date=as_of
    )

@app.get("/health")
def health_check():
    import sqlite3
    import os
    
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'university.db')
    sqlite_status = "ok"
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("SELECT 1")
        conn.close()
    except Exception as e:
        sqlite_status = str(e)
        
    return {
        "api": "ok",
        "chroma": "ok", # mock
        "sqlite": sqlite_status,
        "llm": "ok"     # mock
    }

@app.get("/audit/{trace_id}")
def get_audit_log(trace_id: str):
    audit = get_audit(trace_id)
    if not audit:
        raise HTTPException(status_code=404, detail="Audit log not found")
    return audit

@app.get("/sources")
def get_sources():
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'university.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT doc_id, title, version, effective_from FROM documents")
    rows = cursor.fetchall()
    conn.close()
    return {"sources": [dict(r) for r in rows]}

class LoadRecordsRequest(BaseModel):
    # Dummy structure for loading student records
    records_path: str = Field(..., description="Path to records file (CSV)")

@app.post("/records/load")
def load_records(req: LoadRecordsRequest):
    # Mock implementation of loading records
    return {"status": "success", "message": f"Loaded records from {req.records_path}"}

@app.get("/records/profile")
def get_records_profile(student_id: str = Header(..., description="Student identity header")):
    from app.tools.student_tools import get_profile, GetProfileInput
    res = get_profile(GetProfileInput(student_id=student_id))
    if "error" in res:
        raise HTTPException(status_code=404, detail=res["error"])
    return res["student"]

@app.get("/records/attendance")
def get_records_attendance(student_id: str = Header(..., description="Student identity header"), as_of_date: Optional[str] = None):
    from app.tools.student_tools import get_attendance, GetAttendanceInput, check_exam_eligibility, CheckExamEligibilityInput
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'university.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.course_code, c.course_name, a.classes_held, a.classes_attended
        FROM attendance a
        JOIN courses c ON a.course_code = c.course_code
        WHERE a.student_id = ?
    """, (student_id,))
    rows = cursor.fetchall()
    conn.close()
    
    if not as_of_date:
        as_of_date = datetime.now().strftime("%Y-%m-%d")
        
    records = []
    for r in rows:
        pct = (r['classes_attended'] / r['classes_held']) * 100 if r['classes_held'] > 0 else 0
        elig = check_exam_eligibility(CheckExamEligibilityInput(student_id=student_id, course_code=r['course_code'], as_of_date=as_of_date))
        records.append({
            "course_code": r['course_code'],
            "course_name": r['course_name'],
            "classes_held": r['classes_held'],
            "classes_attended": r['classes_attended'],
            "attendance_pct": pct,
            "eligibility_status": elig.get('status', 'NOT_ELIGIBLE')
        })
    return {"attendance": records}

@app.get("/records/results")
def get_records_results(student_id: str = Header(..., description="Student identity header")):
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'university.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM results WHERE student_id = ?", (student_id,))
    rows = cursor.fetchall()
    conn.close()
    return {"results": [dict(r) for r in rows]}

