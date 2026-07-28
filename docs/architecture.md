# RAG Sentinel – Architecture

## Tech Stack
- Backend: FastAPI (Python)
- Database: SQLite (development) → PostgreSQL (production)
- LLM: Groq (Mixtral 8x7B)
- Frontend: React (planned)
- Deployment: Vercel (backend) + Netlify (frontend)

## Data Flow
1. User submits query, retrieved_docs, answer
2. FastAPI receives request
3. Evaluation pipeline runs:
   a. Alignment Evaluator
   b. Citation Accuracy
   c. Context Contradiction
   d. Factual Consistency
   e. Confidence Calibration
4. Results returned as JSON