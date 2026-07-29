"""
Phase 12.3 (final corrected fix) — HuggingFace Inference Providers
embedding service

The old api-inference.huggingface.co endpoint is deprecated.
HuggingFace now routes all inference through router.huggingface.co
using the "Inference Providers" system.

Uses huggingface_hub's InferenceClient (official library) rather
than raw requests — handles the new routing automatically and is
the officially supported approach going forward.

Dimensions stay at 384 (all-MiniLM-L6-v2) — no FAISS rebuild needed.
"""

from huggingface_hub import InferenceClient

from app.core.config import settings

MODEL = "sentence-transformers/all-MiniLM-L6-v2"


class EmbeddingService:

    _client = None

    @classmethod
    def _get_client(cls) -> InferenceClient:
        if cls._client is None:
            cls._client = InferenceClient(
                provider="hf-inference",
                api_key=getattr(settings, "HF_TOKEN", "") or None
            )
        return cls._client

    @classmethod
    def generate_embedding(cls, text: str) -> list:
        """
        Generate an embedding vector via HuggingFace's Inference
        Providers API (router.huggingface.co under the hood).

        Same signature as the original sentence-transformers version —
        drop-in replacement, no changes needed in calling code.

        Parameters
        ----------
        text : str — text to embed

        Returns
        -------
        list[float] — 384-dimensional embedding vector
        """

        client = cls._get_client()

        result = client.feature_extraction(
            text,
            model=MODEL
        )

        # result is a numpy array — convert to plain list of floats
        # Handle both 1D (single vector) and 2D (token-level) outputs
        arr = result

        # If 2D (per-token embeddings), mean-pool to sentence embedding
        if hasattr(arr, "ndim") and arr.ndim == 2:
            arr = arr.mean(axis=0)

        return arr.tolist() if hasattr(arr, "tolist") else list(arr)