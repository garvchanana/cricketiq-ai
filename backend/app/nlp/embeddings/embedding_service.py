"""
Query/chunk embeddings for semantic retrieval.

Runs the same model the vector index was built with
(sentence-transformers/all-MiniLM-L6-v2, 384 dimensions) inside the server
using ONNX Runtime, instead of calling the Hugging Face Inference API.

Why: the hosted API is metered. Once the free monthly credit is spent it
returns 402 Payment Required and every semantic lookup fails. Running the
model locally has no quota. Measured against the stored index, the vectors
match to four decimal places (cosine 1.0000), so the index needs no rebuild.

The model is loaded on first use and then reused. In Docker it is
downloaded at build time into EMBEDDING_CACHE_DIR so nothing is fetched at
runtime; locally it uses fastembed's default cache folder.
"""

import os
import threading

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


class EmbeddingService:

    _model = None
    _lock = threading.Lock()

    @classmethod
    def _get_model(cls):

        if cls._model is None:
            with cls._lock:
                if cls._model is None:
                    # Imported here so that importing this module stays cheap
                    from fastembed import TextEmbedding

                    cls._model = TextEmbedding(
                        model_name=MODEL_NAME,
                        cache_dir=os.environ.get("EMBEDDING_CACHE_DIR") or None,
                        # One ONNX thread: the free host has a fraction of a
                        # CPU, and extra threads only add memory and overhead.
                        threads=int(os.environ.get("EMBEDDING_THREADS", "1")),
                    )

        return cls._model

    @classmethod
    def generate_embedding(cls, text: str) -> list:
        """
        Embed one piece of text.

        Returns a list of 384 floats. Same signature and return type as the
        previous implementation, so no calling code changes.
        """

        model = cls._get_model()

        vector = next(iter(model.embed([text])))

        return vector.tolist()

    @classmethod
    def generate_embeddings_batch(cls, texts: list) -> list:
        """Embed several texts in one call, preserving input order."""

        if not texts:
            return []

        model = cls._get_model()

        return [vector.tolist() for vector in model.embed(texts)]