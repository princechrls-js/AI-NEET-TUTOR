# AI NEET Coaching Backend

## Project Overview
This project is a FastAPI backend for an AI NEET Coaching platform. It provides a highly modular, production-ready REST API featuring subject-specific (Biology, Chemistry, Physics) Retrieval-Augmented Generation (RAG).

## Folder Explanation
- **app.py**: Application entry point that sets up FastAPI, routes, and data folders.
- **app/api/**: API routing handlers, grouped by features.
- **app/core/**: Core configurations and logging.
- **app/schemas/**: Pydantic models for request/response validation.
- **app/services/**: Core business logic separated by concerns (PDF processing, embeddings, LLM, RAG orchestration).
- **app/utils/**: Utilities such as text cleaning, prompt generation, and metadata mapping.
- **app/data/**: Local file storage for raw data, processed metadata, and FAISS vector indices per subject.

## Installation
1. Install dependencies: `pip install -r requirements.txt`
2. Configure environment: `cp .env.example .env` and populate your `OPENROUTER_API_KEY`.

## How to Run
Ensure you are in the `backend/` directory:
```bash
uvicorn app:app --reload
```

## Sample API Requests
### Health Check
```bash
curl http://localhost:8000/health
```

### Upload PDF to Subject
```bash
curl -X POST "http://localhost:8000/ingest/upload" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@sample_biology.pdf" \
  -F "subject=biology" \
  -F "chapter=cell_structure"
```

### Ask a Question
```bash
curl -X POST "http://localhost:8000/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "subject": "biology",
    "question": "What is the function of mitochondria?",
    "top_k": 3
  }'
```

## Ingestion Flow
1. PDF is uploaded via `/ingest/upload` for a specific subject.
2. Stored locally in `app/data/raw/{subject}/`.
3. PDF content is extracted and cleaned using subject-specific strategies.
4. Chunks are generated (e.g., Biology keeps longer conceptual definitions, whereas Physics isolates formulas).
5. Text chunks are passed to the embedding model.
6. A FAISS index is saved in `app/data/vector_store/{subject}/`.

## Subject-wise RAG Architecture
To prevent mix-ups between domains (e.g., a Physics term confused with Biology), each subject maintains its independent FAISS index. When querying `/ask`:
1. The student specifies a subject.
2. Only the target subject's FAISS index is queried.
3. Relevant chunks build the context for a subject-specific prompt (optimised for NEET answering patterns).
4. The LLM generates the final answer with accurately sourced citations.
