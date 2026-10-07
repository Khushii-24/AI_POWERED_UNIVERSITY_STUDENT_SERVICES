import csv
import sys
import re
import os
from datetime import datetime

RULES_PATH = 'data/rules.csv'
SOURCE_REG_PATH = 'data/source_register.csv'

def validate():
    errors = 0
    
    # Check source_register
    source_docs = set()
    try:
        with open(SOURCE_REG_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                source_docs.add(row['doc_id'])
    except Exception as e:
        print(f"Error reading source register: {e}")
        return 1

    try:
        with open(RULES_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    except Exception as e:
        print(f"Error reading rules: {e}")
        return 1
        
    required_cols = ['rule_id', 'description', 'parameter', 'operator', 'value', 'scope_programmes', 'scope_batches', 'effective_from', 'effective_to', 'source_doc_id', 'source_section', 'source_page', 'source_quote', 'status', 'notes']
    if not all(col in reader.fieldnames for col in required_cols):
        print(f"Missing required columns in rules.csv")
        return 1
        
    rule_ids = set()
    todo_verify = []
    
    for i, row in enumerate(rows, start=2):
        r_id = row['rule_id']
        if r_id in rule_ids:
            print(f"Row {i}: Duplicate rule_id {r_id}")
            errors += 1
        rule_ids.add(r_id)
        
        status = row['status']
        if status == 'TODO_VERIFY':
            todo_verify.append(row)
            
        op = row['operator']
        if op not in ['>=', '>', '<=', '<', '==', 'between']:
            print(f"Row {i}: Invalid operator {op}")
            errors += 1
            
        val = row['value']
        if status == 'CONFIRMED':
            if op == 'between':
                if not re.match(r'^\d+(\.\d+)?;\d+(\.\d+)?$', val):
                    print(f"Row {i}: Invalid between value {val}")
                    errors += 1
            else:
                try:
                    float(val)
                except ValueError:
                    print(f"Row {i}: Invalid value {val}")
                    errors += 1
                    
        # Dates
        try:
            d_from = datetime.strptime(row['effective_from'], '%Y-%m-%d')
            if row['effective_to']:
                d_to = datetime.strptime(row['effective_to'], '%Y-%m-%d')
                if d_to < d_from:
                    print(f"Row {i}: effective_to < effective_from")
                    errors += 1
        except Exception as e:
            print(f"Row {i}: Invalid date format {e}")
            errors += 1
            
        doc_id = row['source_doc_id']
        if doc_id not in source_docs and status == 'CONFIRMED':
            print(f"Row {i}: source_doc_id {doc_id} not in source_register")
            errors += 1
            
        if not row['source_section'] and status == 'CONFIRMED':
            print(f"Row {i}: source_section is empty")
            errors += 1
            
    # Check overlapping windows (simplified check)
    from collections import defaultdict
    param_scopes = defaultdict(list)
    for row in rows:
        if row['status'] == 'CONFIRMED':
            param_scopes[(row['parameter'], row['scope_programmes'], row['scope_batches'])].append(row)
            
    for key, group in param_scopes.items():
        # Sort by effective_from
        group.sort(key=lambda x: x['effective_from'])
        for j in range(len(group)-1):
            curr = group[j]
            nxt = group[j+1]
            if curr['effective_to']:
                if curr['effective_to'] >= nxt['effective_from']:
                    print(f"Overlap detected for {key} between {curr['rule_id']} and {nxt['rule_id']}")
                    errors += 1
            else:
                print(f"Overlap detected for {key} between {curr['rule_id']} (open-ended) and {nxt['rule_id']}")
                errors += 1

    print("\\n--- TODO_VERIFY RULES ---")
    for row in todo_verify:
        print(f"{row['rule_id']} | {row['parameter']} | {row['notes']}")

    if errors > 0:
        print(f"\\nValidation failed with {errors} errors.")
        sys.exit(1)
    else:
        print("\\nValidation passed.")
        
if __name__ == '__main__':
    validate()
