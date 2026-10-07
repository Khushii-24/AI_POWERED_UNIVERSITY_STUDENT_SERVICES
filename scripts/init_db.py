import sqlite3
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'university.db')

def init_db():
    print(f"Initializing database at {DB_PATH}")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    cursor.executescript("""
    -- Documents table
    CREATE TABLE IF NOT EXISTS documents (
        doc_id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        issuer TEXT,
        authority_level INTEGER CHECK (authority_level BETWEEN 1 AND 5),
        doc_type TEXT,
        version TEXT,
        effective_from DATE,
        effective_to DATE,
        supersedes TEXT,
        scope_programmes TEXT,
        scope_batches TEXT,
        provenance TEXT,
        retrieved_on DATETIME
    );

    -- Student table
    CREATE TABLE IF NOT EXISTS student (
        student_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        programme TEXT NOT NULL,
        batch TEXT NOT NULL,
        email TEXT
    );

    -- Courses table
    CREATE TABLE IF NOT EXISTS courses (
        course_code TEXT PRIMARY KEY,
        course_name TEXT NOT NULL,
        programme TEXT NOT NULL,
        semester INTEGER NOT NULL CHECK(semester > 0),
        credits INTEGER NOT NULL CHECK(credits >= 0)
    );

    -- Attendance table
    CREATE TABLE IF NOT EXISTS attendance (
        student_id TEXT NOT NULL,
        course_code TEXT NOT NULL,
        classes_held INTEGER NOT NULL CHECK(classes_held > 0),
        classes_attended INTEGER NOT NULL CHECK(classes_attended >= 0 AND classes_attended <= classes_held),
        PRIMARY KEY (student_id, course_code),
        FOREIGN KEY (student_id) REFERENCES student(student_id),
        FOREIGN KEY (course_code) REFERENCES courses(course_code)
    );

    -- Results table
    CREATE TABLE IF NOT EXISTS results (
        student_id TEXT NOT NULL,
        course_code TEXT NOT NULL,
        exam_session TEXT NOT NULL,
        exam_type TEXT NOT NULL CHECK(exam_type IN ('REGULAR', 'SUPPLEMENTARY')),
        internal_marks REAL CHECK(internal_marks >= 0),
        external_marks REAL CHECK(external_marks >= 0),
        total_marks REAL GENERATED ALWAYS AS (internal_marks + external_marks) VIRTUAL,
        max_marks REAL NOT NULL CHECK(max_marks > 0),
        result TEXT NOT NULL CHECK(result IN ('PASS', 'FAIL', 'ABSENT', 'DETAINED')),
        PRIMARY KEY (student_id, course_code, exam_session, exam_type),
        FOREIGN KEY (student_id) REFERENCES student(student_id),
        FOREIGN KEY (course_code) REFERENCES courses(course_code)
    );

    -- Rule Registry table
    CREATE TABLE IF NOT EXISTS rule_registry (
        rule_id TEXT PRIMARY KEY,
        description TEXT,
        parameter TEXT NOT NULL,
        operator TEXT NOT NULL,
        value TEXT NOT NULL,
        scope_programmes TEXT,
        scope_batches TEXT,
        effective_from DATE,
        effective_to DATE,
        source_doc_id TEXT,
        source_section TEXT,
        FOREIGN KEY (source_doc_id) REFERENCES documents(doc_id)
    );

    -- Audit Log table
    CREATE TABLE IF NOT EXISTS audit_log (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        action TEXT NOT NULL,
        entity_type TEXT NOT NULL,
        entity_id TEXT,
        details TEXT
    );
    """)
    
    conn.commit()
    conn.close()
    print("Database initialization complete.")

if __name__ == "__main__":
    init_db()
