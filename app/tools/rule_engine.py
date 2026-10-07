import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'university.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_rule_with_precedence(rule_id: str, as_of_date: str = None, my_programme: str = None, my_batch: str = None) -> dict:
    if not as_of_date:
        as_of_date = datetime.now().strftime("%Y-%m-%d")
        
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # We might have multiple versions of a rule with the same ID or similar meaning?
    # Based on the schema, rule_id is the PRIMARY KEY, meaning there's only one row per rule_id.
    # Wait, if rule_id is primary key, how do we have multiple versions? 
    # Ah, the prompt says "thresholds ALWAYS read from rule_registry via the precedence logic".
    # Since rule_id is unique, we just fetch it, but we still check applicability (dates, scope).
    
    cursor.execute("""
        SELECT r.*, d.authority_level, d.supersedes
        FROM rule_registry r
        LEFT JOIN documents d ON r.source_doc_id = d.doc_id
        WHERE r.rule_id = ?
    """, (rule_id,))
    
    rule = cursor.fetchone()
    conn.close()
    
    if not rule:
        return None
        
    rule_dict = dict(rule)
    
    # Check scope
    if rule_dict.get('scope_programmes') and my_programme and my_programme not in rule_dict['scope_programmes'].split(','):
        return None
        
    if rule_dict.get('scope_batches') and my_batch and my_batch not in rule_dict['scope_batches'].split(','):
        return None
        
    # Check dates
    effective_from = rule_dict.get('effective_from')
    effective_to = rule_dict.get('effective_to')
    
    if effective_from and effective_from > as_of_date:
        return None
        
    if effective_to and effective_to < as_of_date:
        return None
        
    return rule_dict
