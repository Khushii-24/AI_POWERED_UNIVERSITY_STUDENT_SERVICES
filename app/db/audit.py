import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'university.db')

def log_audit(trace_id: str, data: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    details = json.dumps({
        "question_category": data.get("category"),
        "sources_retrieved": data.get("sources_retrieved", []),
        "precedence_decision": data.get("precedence_decision"),
        "tools_invoked": data.get("tools_invoked", []),
        "rules_applied": data.get("rules_applied", []),
        "conflicts": data.get("conflicts", []),
        "answer_type": data.get("answer_type"),
        "model": data.get("model", "gemini-mock"),
        "llm_calls": data.get("llm_calls", 1),
        "tokens": data.get("tokens", 0),
        "latency_ms": data.get("latency_ms", 0)
    })
    
    cursor.execute("""
        INSERT INTO audit_log (action, entity_type, entity_id, details)
        VALUES (?, ?, ?, ?)
    """, ("ASK_QUERY", "TRACE", trace_id, details))
    
    conn.commit()
    conn.close()

def get_audit(trace_id: str) -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM audit_log
        WHERE entity_type = 'TRACE' AND entity_id = ?
    """, (trace_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return None
        
    return {
        "log_id": row["log_id"],
        "timestamp": row["timestamp"],
        "trace_id": row["entity_id"],
        "details": json.loads(row["details"]) if row["details"] else {}
    }
