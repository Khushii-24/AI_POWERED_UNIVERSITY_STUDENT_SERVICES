# AI-Powered University Student Services

A comprehensive, rule-based AI assistant for university students. Uses a deterministic LangGraph workflow to guarantee adherence to university policies without fabrication.

## Setup Instructions
1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Initialize the database and load synthetic data:
   ```bash
   python scripts/init_db.py
   python scripts/load_records.py
   python scripts/load_rules.py
   ```
4. Run the API:
   ```bash
   uvicorn app.api.main:app --reload
   ```
5. Run the UI (in a separate terminal):
   ```bash
   streamlit run ui/app.py
   ```

## Local LLM Setup (Optional)
```bash
ollama pull llama2
```
Set config switches in `.env` (or mock mode):
- `MOCK_LLM=true` (Default for this MVP)
- `LLM_PROVIDER=ollama`
- `EMBED_MODEL=all-MiniLM-L6-v2`
- `TOP_K=8`
- `OLLAMA_BASE_URL=http://localhost:11434`

## Sample cURL Commands
```bash
# Ask a question
curl -X POST "http://127.0.0.1:8000/ask" \
     -H "Content-Type: application/json" \
     -H "student-id: 123" \
     -d '{"question": "Am I eligible to sit for the CS101 exam?", "as_of_date": "2026-10-07"}'

# Check Health
curl -X GET "http://127.0.0.1:8000/health"
```

## Limitations
- This MVP currently uses a mocked LLM capability within the LangGraph nodes.
- Hybrid vs Dense search tuning requires an active ChromaDB connection.
