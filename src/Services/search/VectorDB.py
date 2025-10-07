"""VectorDB module providing a ChromaDB-backed persistent vector store for email content.

This module defines a production-oriented `VectorDB` class that wraps ChromaDB with:
- Persistent storage at ./vector_store
- SentenceTransformer embedding model (all-MiniLM-L6-v2)
- Methods to add single or multiple emails
- Semantic search capability
- Graceful error handling and logging

Example:
    from Services.search.VectorDB import VectorDB

    vectordb = VectorDB()
    vectordb.add_email("email-1", "Hello this is an example email body")
    results = vectordb.search("example email")
    for r in results:
        print(r)
"""
from __future__ import annotations

import os
import logging
from typing import List, Dict, Any, Iterable, Sequence, Optional, Tuple, Union, cast

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.errors import ChromaError
from sentence_transformers import SentenceTransformer

# Configure module-level logger
logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s %(name)s: %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

DEFAULT_PERSIST_DIR = os.path.abspath("./vector_store")
DEFAULT_COLLECTION = "emails"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

class VectorDB:
    """Persistent ChromaDB-backed vector store for email messages.

    Responsibilities:
        * Initialize (or connect to) a persistent ChromaDB collection
        * Generate embeddings using a SentenceTransformer model
        * Add single or multiple email documents (id + content + optional metadata)
        * Perform similarity search over stored emails

    Thread-safety: Chroma's in-process client is generally thread-safe for reads; if you
    plan heavy concurrent writes, introduce external synchronization.
    """

    def __init__(
        self,
        persist_directory: str = DEFAULT_PERSIST_DIR,
        collection_name: str = DEFAULT_COLLECTION,
        embedding_model_name: str = EMBED_MODEL_NAME,
        create_collection_metadata: Optional[Dict[str, Any]] = None,
        batch_size: int = 32,
        **client_kwargs: Any,
    ) -> None:
        """Create (or load) a persistent vector store.

        Args:
            persist_directory: Directory for Chroma persistent storage.
            collection_name: Name of the Chroma collection.
            embedding_model_name: SentenceTransformer model to load.
            create_collection_metadata: Optional metadata dict for new collection.
            batch_size: Default batch size for embedding operations.
            **client_kwargs: Extra keyword args passed to chromadb.PersistentClient.
        """
        self.persist_directory = os.path.abspath(persist_directory)
        os.makedirs(self.persist_directory, exist_ok=True)
        self.collection_name = collection_name
        self.batch_size = batch_size
        self._embedding_model_name = embedding_model_name

        logger.info(
            "Initializing VectorDB: dir=%s collection=%s model=%s", 
            self.persist_directory, self.collection_name, self._embedding_model_name
        )

        try:
            self.client = chromadb.PersistentClient(path=self.persist_directory, **client_kwargs)
        except Exception as exc:  # Broad catch to log environment issues
            logger.exception("Failed to initialize Chroma PersistentClient: %s", exc)
            raise

        # Create (or load) collection
        metadata = create_collection_metadata or {"description": "Email semantic store"}
        try:
            self.collection: Collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata=metadata,
            )
        except Exception as exc:
            logger.exception("Failed to get or create collection '%s': %s", self.collection_name, exc)
            raise

        # Lazy-load embedding model (loaded once) 
        try:
            # Explicitly use CPU device
            self._embedder = SentenceTransformer(self._embedding_model_name, device='cpu')
        except Exception as exc:
            logger.exception("Failed to load embedding model '%s': %s", self._embedding_model_name, exc)
            raise

    # ---------------------------- Internal helpers ------------------------- #
    def _embed_batch(self, texts: Sequence[str]) -> List[List[float]]:
        """Embed a batch of texts returning a list of embedding vectors.

        Uses SentenceTransformer.encode with show_progress_bar disabled for efficiency.
        Raises RuntimeError if embedding fails.
        """
        if not texts:
            return []
        try:
            embeddings = self._embedder.encode(list(texts), show_progress_bar=False, batch_size=self.batch_size)
            # Ensure list of lists (convert np.ndarray if necessary)
            return [e.tolist() if hasattr(e, 'tolist') else list(e) for e in embeddings]
        except Exception as exc:
            logger.exception("Embedding batch failed: %s", exc)
            raise RuntimeError(f"Embedding failed: {exc}") from exc

    # ---------------------------- Public API -------------------------------- #
    def add_email(
        self,
        email_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        upsert: bool = True,
    ) -> None:
        """Add (or upsert) a single email into the vector store.

        Args:
            email_id: Unique identifier for the email (must be unique in collection).
            content: Raw textual content of the email.
            metadata: Optional metadata dictionary (e.g., sender, subject, date).
            upsert: If True, existing id will be overwritten (Chroma allows duplicate IDs unless handled).
        """
        if not email_id:
            raise ValueError("email_id is required")
        if not content:
            raise ValueError("content is empty")

        # In Chroma, adding a duplicate ID raises an error unless using update semantics. We mimic upsert.
        if not upsert:
            # Best-effort existence check
            existing = self.collection.get(ids=[email_id])
            if existing and existing.get("ids"):
                raise ValueError(f"ID '{email_id}' already exists and upsert is False")

        embeddings = self._embed_batch([content])
        try:
            # Chroma type stubs can be strict; cast to acceptable union types
            self.collection.add(
                ids=[email_id],
                documents=[content],
                embeddings=cast(Any, embeddings),  # runtime accepts list[list[float]]
                metadatas=cast(Any, [metadata or {}]),
            )
            logger.debug("Added email id=%s", email_id)
        except ChromaError as ce:
            logger.error("ChromaError while adding email %s: %s", email_id, ce)
            raise
        except Exception as exc:
            logger.exception("Unexpected error adding email %s: %s", email_id, exc)
            raise

    def add_emails(
        self,
        emails: Iterable[Tuple[str, str]],
        metadatas: Optional[Iterable[Dict[str, Any]]] = None,
        upsert: bool = True,
        batch_size: Optional[int] = None,
    ) -> int:
        """Batch add multiple emails efficiently.

        Args:
            emails: Iterable of (email_id, content) tuples.
            metadatas: Iterable of metadata dicts (aligned with emails) or None for empty dicts.
            upsert: Control duplicate handling similar to add_email.
            batch_size: Override default embedding batch size for this call.

        Returns:
            Number of emails successfully added.
        """
        email_list = list(emails)
        if not email_list:
            return 0

        meta_list: List[Dict[str, Any]]
        if metadatas is None:
            meta_list = [{} for _ in email_list]
        else:
            meta_list = list(metadatas)
            if len(meta_list) != len(email_list):
                raise ValueError("Length of metadatas must match length of emails")

        # Optional upsert check (may cost an extra round-trip if many ids). For large scale, rely on upsert semantics.
        if not upsert:
            existing_ids = []
            for eid, _ in email_list:
                try:
                    res = self.collection.get(ids=[eid])
                    if res and res.get("ids"):
                        existing_ids.append(eid)
                except Exception:  # Non-fatal
                    continue
            if existing_ids:
                raise ValueError(f"Existing IDs prevent insert (upsert=False): {existing_ids[:5]}{'...' if len(existing_ids)>5 else ''}")

        bs = batch_size or self.batch_size
        added = 0
        # Process in batches for embedding efficiency
        for i in range(0, len(email_list), bs):
            chunk = email_list[i : i + bs]
            ids = [eid for eid, _ in chunk]
            docs = [content for _, content in chunk]
            metas = meta_list[i : i + bs]
            embeddings = self._embed_batch(docs)
            try:
                self.collection.add(
                    ids=ids,
                    documents=docs,
                    embeddings=cast(Any, embeddings),
                    metadatas=cast(Any, metas),
                )
                added += len(ids)
            except ChromaError as ce:
                logger.error("ChromaError during batch add (ids sample %s): %s", ids[:3], ce)
                # Decide whether to continue or halt; here we halt to avoid silent data loss.
                raise
            except Exception as exc:
                logger.exception("Unexpected error during batch add: %s", exc)
                raise
        logger.info("Added %d emails (batch size=%d)", added, bs)
        return added

    def search(
        self,
        query: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        include: Optional[Sequence[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Semantic similarity search over stored emails.

        Args:
            query: Natural language query text.
            n_results: Number of results to return (default 5).
            where: Optional Chroma metadata filter dict.
            include: Additional fields to include (e.g., ["metadatas", "distances"]).

        Returns:
            A list of result dicts with keys: id, document, metadata, distance (if requested).
        """
        if not query:
            raise ValueError("query is empty")
        try:
            q_embedding = self._embed_batch([query])[0]
        except Exception as exc:
            raise RuntimeError(f"Failed to embed query: {exc}") from exc

        try:
            include_arg: List[str]
            if include is None:
                include_arg = ["metadatas", "distances", "documents"]
            else:
                include_arg = list(include)
            results = self.collection.query(
                query_embeddings=[q_embedding],
                n_results=n_results,
                where=where,
                include=cast(Any, include_arg),
            )
        except ChromaError as ce:
            logger.error("ChromaError during search: %s", ce)
            raise
        except Exception as exc:
            logger.exception("Unexpected error during search: %s", exc)
            raise

        # Repackage results
        packaged: List[Dict[str, Any]] = []
        ids_raw = results.get("ids") or [[]]
        docs_raw = results.get("documents") or [[]]
        metas_raw = results.get("metadatas") or [[]]
        dists_raw = results.get("distances") or [[]]
        ids = ids_raw[0] if ids_raw else []
        docs = docs_raw[0] if docs_raw else []
        metas = metas_raw[0] if metas_raw else []
        dists = dists_raw[0] if dists_raw else []
        for i, _id in enumerate(ids):
            packaged.append(
                {
                    "id": _id,
                    "document": docs[i] if i < len(docs) else None,
                    "metadata": metas[i] if i < len(metas) else None,
                    "distance": dists[i] if i < len(dists) else None,
                }
            )
        return packaged

    # ---------------------------- Utility methods -------------------------- #
    def __len__(self) -> int:
        """Return approximate number of stored emails.

        Tries collection.count() if available; otherwise falls back to fetching ids.
        """
        try:
            if hasattr(self.collection, 'count'):
                return int(getattr(self.collection, 'count')())  # type: ignore[call-arg]
        except Exception:
            pass
        try:
            data = self.collection.get()
            return len(data.get("ids", []))
        except Exception:
            return 0

    def delete_email(self, email_id: str) -> bool:
        """Delete a single email from the vector store.

        Args:
            email_id: Unique identifier for the email to delete

        Returns:
            True if email was successfully deleted or didn't exist, False on error
        """
        try:
            logger.debug(f"Deleting email from vector store: {email_id}")
            
            # Check if email exists first
            existing = self.collection.get(ids=[email_id])
            if not existing["ids"]:
                logger.debug(f"Email {email_id} not found in vector store (already deleted)")
                return True
            
            # Delete the email
            self.collection.delete(ids=[email_id])
            logger.info(f"Successfully deleted email {email_id} from vector store")
            return True
            
        except ChromaError as e:
            logger.error(f"ChromaDB error deleting email {email_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting email {email_id}: {e}")
            return False

    def delete_emails(self, email_ids: List[str]) -> Dict[str, Any]:
        """Delete multiple emails from the vector store in batch.

        Args:
            email_ids: List of email IDs to delete

        Returns:
            Dictionary with deletion results:
            {
                "successful": int,  # Number of successfully deleted emails
                "failed": int,      # Number of failed deletions
                "errors": List[str] # Error messages for failed deletions
            }
        """
        if not email_ids:
            return {"successful": 0, "failed": 0, "errors": []}

        logger.info(f"Starting batch deletion of {len(email_ids)} emails")
        
        try:
            # Check which emails exist
            existing = self.collection.get(ids=email_ids)
            existing_ids = set(existing["ids"])
            
            # Filter to only delete existing emails
            emails_to_delete = [eid for eid in email_ids if eid in existing_ids]
            
            if not emails_to_delete:
                logger.info("No emails found to delete (all already deleted)")
                return {"successful": len(email_ids), "failed": 0, "errors": []}
            
            # Perform batch deletion
            self.collection.delete(ids=emails_to_delete)
            
            successful = len(emails_to_delete)
            not_found = len(email_ids) - successful
            
            logger.info(f"Batch deletion completed: {successful} deleted, {not_found} not found")
            
            return {
                "successful": len(email_ids),  # Consider not-found as successful
                "failed": 0,
                "errors": []
            }
            
        except ChromaError as e:
            error_msg = f"ChromaDB batch deletion error: {e}"
            logger.error(error_msg)
            return {
                "successful": 0,
                "failed": len(email_ids),
                "errors": [error_msg]
            }
        except Exception as e:
            error_msg = f"Unexpected batch deletion error: {e}"
            logger.error(error_msg)
            return {
                "successful": 0,
                "failed": len(email_ids),
                "errors": [error_msg]
            }

    def email_exists(self, email_id: str) -> bool:
        """Check if an email exists in the vector store.

        Args:
            email_id: Email ID to check

        Returns:
            True if email exists, False otherwise
        """
        try:
            existing = self.collection.get(ids=[email_id])
            return len(existing["ids"]) > 0
        except Exception as e:
            logger.error(f"Error checking if email {email_id} exists: {e}")
            return False

    def get_email_count(self) -> int:
        """Get the total number of emails in the vector store.

        Returns:
            Number of emails in the store
        """
        return len(self)

__all__ = ["VectorDB"]
