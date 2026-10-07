import json
import time
import os
import statistics
import requests

EVAL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'eval')
API_URL = "http://127.0.0.1:8000/ask"
STUDENT_ID = "123"

def run_eval():
    with open(os.path.join(EVAL_DIR, 'questions.json'), 'r') as f:
        questions = json.load(f)

    results = []
    latencies = []
    
    correct_type = 0
    total = len(questions)

    print("Running evaluation...")
    for q in questions:
        print(f"Testing: {q['id']} - {q['category']}")
        start_time = time.time()
        
        try:
            # Assume API is running for true eval, but we could also invoke workflow directly
            # For this MVP, we will invoke the workflow directly to avoid needing the server running
            from app.workflow.graph import build_workflow
            import uuid
            
            workflow = build_workflow()
            state = {
                "trace_id": str(uuid.uuid4()),
                "question": q['question'],
                "as_of_date": "2026-10-07",
                "student_id": STUDENT_ID,
                "student_programme": "BTECH",
                "student_batch": "2024"
            }
            
            res = workflow.invoke(state)
            latency = (time.time() - start_time) * 1000
            latencies.append(latency)
            
            actual_type = res.get('answer_type')
            is_correct = (actual_type == q['expected_answer_type'])
            if is_correct:
                correct_type += 1
                
            results.append({
                "id": q['id'],
                "question": q['question'],
                "expected_type": q['expected_answer_type'],
                "actual_type": actual_type,
                "is_correct": is_correct,
                "latency_ms": latency
            })
        except Exception as e:
            print(f"Error on {q['id']}: {e}")
            
    # Calculate metrics
    accuracy = (correct_type / total) * 100 if total > 0 else 0
    p50 = statistics.median(latencies) if latencies else 0
    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max(latencies) if latencies else 0
    
    report_content = f"""# Evaluation Report

## Summary
- **Total Questions Evaluated**: {total}
- **Type Accuracy**: {accuracy:.2f}%
- **p50 Latency**: {p50:.2f} ms
- **p95 Latency**: {p95:.2f} ms

## Detailed Results
| ID | Category | Expected Type | Actual Type | Result | Latency (ms) |
|---|---|---|---|---|---|
"""
    for r in results:
        status = "✅ Pass" if r['is_correct'] else "❌ Fail"
        report_content += f"| {r['id']} | {q['category']} | {r['expected_type']} | {r['actual_type']} | {status} | {r['latency_ms']:.2f} |\n"

    report_path = os.path.join(EVAL_DIR, 'report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
        
    print(f"Evaluation complete. Report generated at {report_path}")

if __name__ == "__main__":
    run_eval()
