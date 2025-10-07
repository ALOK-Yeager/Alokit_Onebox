#!/usr/bin/env python3
"""
main.py: FastAPI service for RAG-based email reply generation.
"""
import os
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.logger import logger
from pydantic import BaseModel
import uvicorn
from typing import Any

# Lazy import of RAGSystem inside startup to prevent early import errors
# from rag_service import RAGSystem

# Load environment variables from .env
load_dotenv()
# Retrieve calendar link
CAL_COM_LINK = os.getenv("CAL_COM_LINK", "<your_calendar_link_here>")

# Pydantic models for request and response
class ReplyRequest(BaseModel):
    email_body: str

class ReplyResponse(BaseModel):
    reply: str

# Initialize FastAPI app
app = FastAPI(
    title="RAG Email Reply Service",
    description="Generate intelligent email replies via Retrieval-Augmented Generation",
    version="1.0.0"
)

# Global RAG system instance
rag_system: Any = None

@app.on_event("startup")
def startup_event():
    """Initialize RAG system and preload default templates."""
    global rag_system
    try:
        # Import RAGSystem here to defer heavy dependencies
        from rag_service import RAGSystem
        rag_system = RAGSystem()
        # Preload example templates
        rag_system.add_document(
            (
                "Hello {name},\n\n"
                "Thank you for reaching out. I'd like to schedule a meeting to discuss further. "
                f"Please book a time using this link: {CAL_COM_LINK}.\n\n"
                "Looking forward to our conversation.\n\nBest regards,\n{name}"
            ),
            {"template": "meeting_scheduling"}
        )
        rag_system.add_document(
            (
                "Dear {name},\n\n"
                "Thank you for your inquiry. Unfortunately, we are unable to accommodate your request at this time. "
                "We appreciate your understanding and hope to connect in the future.\n\n"
                "Sincerely,\n{name}"
            ),
            {"template": "polite_rejection"}
        )
    except Exception as e:
        logger.error(f"Error initializing RAG system: {e}")
        rag_system = None  # Ensure rag_system is defined

@app.post("/generate-reply", response_model=ReplyResponse)
def generate_reply(request: ReplyRequest):
    """Generate an AI reply for the provided email body."""
    try:
        reply_text = rag_system.generate_reply(request.email_body)
        return ReplyResponse(reply=reply_text)
    except Exception as e:
        # Return HTTP 500 on failure
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    # Run the app on localhost:8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info")
