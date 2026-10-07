import chromadb
from chromadb.config import Settings
import os

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'data', 'chroma_db')
os.makedirs(DB_DIR, exist_ok=True)

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=DB_DIR)
        # Using default sentence-transformers embedding function (all-MiniLM-L6-v2) for now
        # To use BAAI/bge-small-en-v1.5, we can specify it in the embedding function
        from chromadb.utils import embedding_functions
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="BAAI/bge-small-en-v1.5")
        
        self.collection = self.client.get_or_create_collection(
            name="university_docs",
            embedding_function=self.emb_fn
        )
        
    def add_chunks(self, chunks, doc_id):
        # Delete existing chunks for this doc_id to avoid duplicates if re-ingesting
        self.collection.delete(where={"doc_id": doc_id})
        
        if not chunks:
            return
            
        ids = [f"{doc_id}_{i}" for i in range(len(chunks))]
        documents = [c['text'] for c in chunks]
        
        # Ensure metadata values are strings, ints, floats, or bools
        metadatas = []
        for c in chunks:
            clean_meta = {}
            for k, v in c['metadata'].items():
                if v is not None:
                    clean_meta[k] = str(v) if not isinstance(v, (int, float, bool, str)) else v
            metadatas.append(clean_meta)
            
        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

vector_store = VectorStore()
