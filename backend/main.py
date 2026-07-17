"""
backend/main.py
----------------
FastAPI application entry point.

Run with (from the project ROOT folder, not inside backend/):
    uvicorn backend.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routes import router

app = FastAPI(
    title="Sherlock - Candidate Identification API",
    description="Identifies the real interview candidate in a live call using multi-signal confidence scoring.",
    version="1.0.0",
)

# Allow the Streamlit frontend (different port) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {"message": "Sherlock Candidate Identification API is running. See /docs for API docs."}
