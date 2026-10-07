import csv
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'university.db')
RULES_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'rules.csv')

def load_rules():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    skipped = []
    loaded = 0
    
    with open(RULES_PATH, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['status'] != 'CONFIRMED':
                skipped.append(row['rule_id'])
                continue
                
            cursor.execute(\"\"\"
                INSERT INTO rule_registry
                (rule_id, description, parameter, operator, value, scope_programmes, scope_batches, effective_from, effective_to, source_doc_id, source_section)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(rule_id) DO UPDATE SET
                description=excluded.description,
                parameter=excluded.parameter,
                operator=excluded.operator,
                value=excluded.value,
                scope_programmes=excluded.scope_programmes,
                scope_batches=excluded.scope_batches,
                effective_from=excluded.effective_from,
                effective_to=excluded.effective_to,
                source_doc_id=excluded.source_doc_id,
                source_section=excluded.source_section
            \"\"\", (
                row['rule_id'], row['description'], row['parameter'], row['operator'], row['value'],
                row['scope_programmes'], row['scope_batches'], row['effective_from'], row['effective_to'],
                row['source_doc_id'], row['source_section']
            ))
            loaded += 1
            
    conn.commit()
    conn.close()
    
    print(f"Loaded {loaded} CONFIRMED rules.")
    if skipped:
        print("Skipped TODO_VERIFY rules:")
        for rule_id in skipped:
            print(f"- {rule_id}")

if __name__ == '__main__':
    load_rules()
