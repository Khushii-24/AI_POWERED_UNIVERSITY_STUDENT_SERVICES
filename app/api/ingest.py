from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks
import json
import sqlite3
import os
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

from app.rag.parser import parse_document, chunk_document
from app.rag.vectorstore import vector_store

router = APIRouter()

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'university.db')

class IngestMetadata(BaseModel):
    doc_id: str
    title: str
    issuer: Optional[str] = None
    authority_level: int
    doc_type: Optional[str] = None
    version: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    supersedes: Optional[str] = None
    scope_programmes: Optional[str] = None
    scope_batches: Optional[str] = None
    rules: Optional[List[Dict]] = None

def process_ingestion(metadata: IngestMetadata, file_content: bytes, file_name: str):
    # Parse and chunk
    pages = parse_document(file_name, file_content)
    
    meta_dict = metadata.model_dump(exclude={'rules'})
    meta_dict['retrieved_on'] = datetime.now().isoformat()
    
    chunks = chunk_document(pages, meta_dict)
    
    # Store in DB
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if doc exists, if so delete it (re-ingesting replaces it)
        cursor.execute("DELETE FROM documents WHERE doc_id=?", (metadata.doc_id,))
        
        cursor.execute(\"\"\"
            INSERT INTO documents 
            (doc_id, title, issuer, authority_level, doc_type, version, effective_from, effective_to, supersedes, scope_programmes, scope_batches, provenance, retrieved_on)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        \"\"\", (
            metadata.doc_id, metadata.title, metadata.issuer, metadata.authority_level, metadata.doc_type,
            metadata.version, metadata.effective_from, metadata.effective_to, metadata.supersedes,
            metadata.scope_programmes, metadata.scope_batches, file_name, meta_dict['retrieved_on']
        ))
        
        if metadata.rules:
            for rule in metadata.rules:
                cursor.execute(\"\"\"
                    INSERT INTO rule_registry
                    (rule_id, description, parameter, operator, value, scope_programmes, scope_batches, effective_from, effective_to, source_doc_id, source_section)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                \"\"\", (
                    rule['rule_id'], rule.get('description'), rule['parameter'], rule['operator'], rule['value'],
                    rule.get('scope_programmes'), rule.get('scope_batches'), rule.get('effective_from'), rule.get('effective_to'),
                    metadata.doc_id, rule.get('source_section')
                ))
                
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()
        
    vector_store.add_chunks(chunks, metadata.doc_id)
    print(f"Successfully ingested {metadata.doc_id} into SQLite and VectorStore.")

@router.post("/ingest")
async def ingest_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    metadata: str = Form(...)
):
    try:
        meta_dict = json.loads(metadata)
        ingest_meta = IngestMetadata(**meta_dict)
    except Exception as e:
        return {"error": f"Invalid metadata JSON: {str(e)}"}
        
    file_content = await file.read()
    
    # Process synchronously for now to ensure it's available immediately
    # Could be moved to background_tasks for large files
    process_ingestion(ingest_meta, file_content, file.filename)
    
    return {"message": f"Successfully ingested {ingest_meta.doc_id}", "doc_id": ingest_meta.doc_id}
