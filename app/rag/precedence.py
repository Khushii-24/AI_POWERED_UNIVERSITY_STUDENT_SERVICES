import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'university.db')

def get_doc_metadata(doc_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents WHERE doc_id = ?", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else {}

def resolve_precedence(chunks, as_of_date=None, my_programme=None, my_batch=None):
    """
    Precedence logic for retrieved chunks.
    """
    if as_of_date is None:
        as_of_date = datetime.now().strftime("%Y-%m-%d")
        
    # Group chunks by doc_id to fetch metadata
    doc_ids = list(set([c['metadata']['doc_id'] for c in chunks]))
    docs_metadata = {doc_id: get_doc_metadata(doc_id) for doc_id in doc_ids}
    
    # 1. Applicability & Scope
    applicable_chunks = []
    upcoming_changes = []
    
    for chunk in chunks:
        doc_id = chunk['metadata']['doc_id']
        meta = docs_metadata.get(doc_id, {})
        
        # Check scope
        scope_progs = meta.get('scope_programmes')
        if scope_progs and my_programme and my_programme not in scope_progs.split(','):
            continue
            
        scope_batches = meta.get('scope_batches')
        if scope_batches and my_batch and my_batch not in scope_batches.split(','):
            continue
            
        # Check effective dates
        effective_from = meta.get('effective_from')
        effective_to = meta.get('effective_to')
        
        if effective_from and effective_from > as_of_date:
            upcoming_changes.append(chunk)
            continue
            
        if effective_to and effective_to < as_of_date:
            continue # expired
            
        applicable_chunks.append((chunk, meta))
        
    # 2. Explicit supersession
    # Map of doc_id -> list of chunks
    superseded_docs = set()
    for _, meta in applicable_chunks:
        if meta.get('authority_level') in (1, 2) and meta.get('supersedes'):
            superseded_docs.update([s.strip() for s in meta['supersedes'].split(',')])
            
    filtered_by_supersession = [(c, m) for c, m in applicable_chunks if m.get('doc_id') not in superseded_docs]
    
    if not filtered_by_supersession:
        return {
            "chunks": [],
            "precedence_decision": "No applicable sources found.",
            "conflicts": [],
            "upcoming_changes": upcoming_changes,
            "answer_type": "no_info"
        }
        
    # 3 & 4. Authority and Date precedence
    # To detect conflicts, let's say a conflict happens if two chunks from different docs talk about the same section/topic
    # Since we can't perfectly know topic, we'll assume chunks returned for a query are on the same topic.
    # We group by authority, then by date.
    
    # Sort by authority level (ascending, so lower number/higher authority first), then by effective_from (descending)
    def sort_key(item):
        m = item[1]
        auth = m.get('authority_level') or 5
        date = m.get('effective_from') or '1900-01-01'
        return (auth, -int(date.replace('-', '')))
        
    sorted_chunks = sorted(filtered_by_supersession, key=sort_key)
    
    # Best doc
    best_chunk, best_meta = sorted_chunks[0]
    best_auth = best_meta.get('authority_level') or 5
    best_date = best_meta.get('effective_from') or '1900-01-01'
    
    winning_chunks = []
    conflicts = []
    
    for c, m in sorted_chunks:
        auth = m.get('authority_level') or 5
        date = m.get('effective_from') or '1900-01-01'
        
        if auth == best_auth and date == best_date:
            winning_chunks.append(c)
        elif auth == best_auth and date != best_date:
            # Different dates, lower date is superseded by higher date
            pass
        else:
            # Lower authority. Does it conflict?
            # For this MVP, if there is a level 1 doc and a level 4 doc, the level 1 doc wins.
            pass
            
    # Check if there are multiple winners from DIFFERENT docs (unresolved conflict)
    winner_doc_ids = set([c['metadata']['doc_id'] for c in winning_chunks])
    
    if len(winner_doc_ids) > 1:
        # Conflict!
        conflicts = [c['metadata']['doc_id'] for c in winning_chunks]
        return {
            "chunks": winning_chunks,
            "precedence_decision": "Multiple sources with same authority and date found.",
            "conflicts": conflicts,
            "upcoming_changes": upcoming_changes,
            "answer_type": "conflict_flagged"
        }
        
    return {
        "chunks": winning_chunks,
        "precedence_decision": f"Source {best_meta.get('doc_id')} selected based on authority {best_auth} and date {best_date}.",
        "conflicts": [],
        "upcoming_changes": upcoming_changes,
        "answer_type": "standard"
    }

def retrieve_and_resolve(query, top_k=8, as_of_date=None, my_programme=None, my_batch=None):
    from app.rag.vectorstore import vector_store
    
    results = vector_store.collection.query(
        query_texts=[query],
        n_results=top_k
    )
    
    if not results['documents'] or not results['documents'][0]:
        return {
            "chunks": [],
            "precedence_decision": "No matching documents found.",
            "conflicts": [],
            "upcoming_changes": [],
            "answer_type": "no_info"
        }
        
    chunks = []
    for i in range(len(results['documents'][0])):
        chunks.append({
            "text": results['documents'][0][i],
            "metadata": results['metadatas'][0][i]
        })
        
    return resolve_precedence(chunks, as_of_date, my_programme, my_batch)
