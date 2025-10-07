#!/usr/bin/env python3
"""
rag_service.py: Core logic for RAG-based email reply generator using ChromaDB, Sentence-Transformers, and Groq LLM.
"""

import os
# Suppress TensorFlow info logs and protobuf warnings
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
import logging
logging.getLogger('tensorflow').setLevel(logging.ERROR)
import warnings
import uuid
import warnings

import chromadb

from sentence_transformers import SentenceTransformer

import groq
from typing import Any

# Add filter to suppress protobuf version warnings
warnings.filterwarnings("ignore", r"Protobuf gencode version.*")


class RAGSystem:
    def __init__(self):
        """Initialize embedding model, ChromaDB client and collection."""
        # Load embedding model
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
        # Initialize ChromaDB client (in-memory default)
        self.client = chromadb.Client()
        # Create or get a collection for our documents
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"description": "Email reply templates and knowledge snippets"}
        )

    def add_document(self, text: str, metadata: dict):
        """Add a document to ChromaDB with embedding and metadata."""
        # Generate unique ID for the document
        doc_id = str(uuid.uuid4())
        # Encode text to embedding vector
        embedding = self.embedding_model.encode(text).tolist()
        # Add document to the collection
        self.collection.add(
            ids=[doc_id],
            documents=[text],
            embeddings=[embedding],
            metadatas=[metadata],
        )

    def find_relevant_documents(self, query_text: str, top_k: int = 3):
        """Retrieve top_k relevant documents from ChromaDB for the query."""
        # Encode query to embedding vector
        query_embedding = self.embedding_model.encode(query_text).tolist()
        # Query the collection for similar embeddings
        results: Any = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
        )
        # Extract documents and their metadata
        docs = results["documents"][0]
        metadatas = results["metadatas"][0]
        return list(zip(docs, metadatas))

    def generate_reply(self, email_body: str) -> str:
        """Generate an AI reply for the given email body."""
        # Step 1: Retrieve relevant context documents
        relevant = self.find_relevant_documents(email_body)
        # Step 2: Prepare prompt for LLM
        context_str = ""
        for idx, (doc, meta) in enumerate(relevant, start=1):
            context_str += f"Template {idx} (metadata: {meta}):\n{doc}\n\n"
        prompt = (
            "You are an intelligent email assistant.\n\n"
            f"Incoming Email:\n{email_body}\n\n"
            "Context Templates:\n"
            f"{context_str}"
            "Please compose a professional reply to the incoming email, using the above templates as guidance where appropriate.\n\n"
            "Reply:"
        )
        # Step 3: Call Groq LLM API
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise EnvironmentError("GROQ_API_KEY environment variable not set.")
        # Initialize Groq client
        client: Any = groq.Client(api_key=api_key)
        # Generate response from LLM
        response = client.generate(
            model="llama3-8b-8192",
            prompt=prompt
        )
        # Parse and return the generated reply text
        text = response["choices"][0]["text"]
        return text.strip()


if __name__ == "__main__":
    # Example usage of RAGSystem
    rag = RAGSystem()
    # Add example templates
    rag.add_document(
        "Hello {name},\n\nThank you for your email. I would like to schedule a meeting on {date} at {time}. Please let me know if this works for you.\n\nBest regards,\n{name}",
        {"template": "meeting_scheduling"}
    )
    rag.add_document(
        "Dear {name},\n\nThank you for considering us. Unfortunately, we are unable to proceed with your request at this time. We appreciate your understanding.\n\nSincerely,\n{name}",
        {"template": "polite_rejection"}
    )
    # Simulate incoming email
    incoming_email = (
        "Hi,\n\nI hope you are doing well. "
        "Could we set up a meeting next week to discuss the project timeline? "
        "Please let me know your availability.\n\nThanks,\nJohn"
    )
    # Generate and print reply
    reply = rag.generate_reply(incoming_email)
    print("Generated Reply:\n", reply)
