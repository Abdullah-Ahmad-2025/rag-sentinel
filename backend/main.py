from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.evaluate import router as evaluate_router
from backend.api.upload import router as upload_router
from backend.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="RAG Sentinel", lifespan=lifespan)

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


app.include_router(evaluate_router)
app.include_router(upload_router)
