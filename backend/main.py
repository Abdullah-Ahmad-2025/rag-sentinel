from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import the evaluate router
from backend.api.evaluate import router as evaluate_router

app = FastAPI(title="RAG Sentinel")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "RAG Sentinel API is running"}

@app.get("/health")
def health():
    return {"status": "ok", "message": "RAG Sentinel backend is healthy"}

# Include the evaluate router
app.include_router(evaluate_router)