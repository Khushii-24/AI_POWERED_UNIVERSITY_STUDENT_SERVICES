import csv
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'university.db')
TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'templates')

def load_records():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()
    
    violations = []
    
    # 1. Load Students
    student_file = os.path.join(TEMPLATES_DIR, 'students.csv')
    if os.path.exists(student_file):
        with open(student_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO student (student_id, name, programme, batch, email)
                        VALUES (?, ?, ?, ?, ?)
                    """, (row['student_id'], row['name'], row['programme'], row['batch'], row['email']))
                except sqlite3.Error as e:
                    violations.append(f"Student Insert Error ({row['student_id']}): {str(e)}")
                    
    # 2. Load Courses
    course_file = os.path.join(TEMPLATES_DIR, 'courses.csv')
    if os.path.exists(course_file):
        with open(course_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    cursor.execute("""
                        INSERT OR REPLACE INTO courses (course_code, course_name, programme, semester, credits)
                        VALUES (?, ?, ?, ?, ?)
                    """, (row['course_code'], row['course_name'], row['programme'], row['semester'], row['credits']))
                except sqlite3.Error as e:
                    violations.append(f"Course Insert Error ({row['course_code']}): {str(e)}")
                    
    # 3. Load Attendance
    att_file = os.path.join(TEMPLATES_DIR, 'attendance.csv')
    if os.path.exists(att_file):
        with open(att_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    held = int(row['classes_held'])
                    attended = int(row['classes_attended'])
                    if attended > held:
                        violations.append(f"Attendance Validation Error ({row['student_id']}, {row['course_code']}): attended ({attended}) > held ({held})")
                        continue
                        
                    cursor.execute("""
                        INSERT OR REPLACE INTO attendance (student_id, course_code, classes_held, classes_attended)
                        VALUES (?, ?, ?, ?)
                    """, (row['student_id'], row['course_code'], held, attended))
                except Exception as e:
                    violations.append(f"Attendance Insert Error ({row['student_id']}, {row['course_code']}): {str(e)}")

    # 4. Load Results
    res_file = os.path.join(TEMPLATES_DIR, 'results.csv')
    if os.path.exists(res_file):
        with open(res_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    int_marks = float(row['internal_marks'])
                    ext_marks = float(row['external_marks'])
                    max_marks = float(row['max_marks'])
                    total = int_marks + ext_marks
                    if total > max_marks:
                        violations.append(f"Results Validation Error ({row['student_id']}, {row['course_code']}): total ({total}) > max ({max_marks})")
                        continue
                        
                    cursor.execute("""
                        INSERT OR REPLACE INTO results (student_id, course_code, exam_session, exam_type, internal_marks, external_marks, max_marks, result)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (row['student_id'], row['course_code'], row['exam_session'], row['exam_type'], int_marks, ext_marks, max_marks, row['result']))
                except Exception as e:
                    violations.append(f"Results Insert Error ({row['student_id']}, {row['course_code']}): {str(e)}")
                    
    conn.commit()
    conn.close()
    
    if violations:
        print("Data Loading Violations Detected:")
        for v in violations:
            print(f"- {v}")
    else:
        print("All records loaded successfully with no violations.")

if __name__ == '__main__':
    load_records()
