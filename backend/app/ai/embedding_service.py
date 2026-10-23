"""
app/ai/embedding_service.py
============================
Isolated embedding utilities for CampusHire.

Provides:
  - get_embedding_model()  -> SentenceTransformer singleton (cached)
  - generate_embedding(text) -> list[float]
  - cosine_similarity_score(a, b) -> float  (0-100)

Custom exceptions:
  - EmbeddingGenerationError  (raised for empty/whitespace input or model failures)

No FastAPI routes or SQLAlchemy models are imported here.
Model name is configurable via the EMBEDDING_MODEL_NAME env var.
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration: model name from env (via settings), defaulting to a small
# CPU-friendly model.
# ---------------------------------------------------------------------------
try:
    from app.core.config import settings
    _MODEL_NAME: str = getattr(settings, "EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
except Exception:
    _MODEL_NAME = "all-MiniLM-L6-v2"

# ---------------------------------------------------------------------------
# Module-level singleton — loaded once, reused forever.
# ---------------------------------------------------------------------------
_MODEL_INSTANCE = None  # type: Optional["SentenceTransformer"]


# ===========================================================================
# Custom Exceptions
# ===========================================================================


class EmbeddingGenerationError(Exception):
    """
    Raised when embedding generation fails.

    Causes:
    - Input text is empty or whitespace-only.
    - The SentenceTransformer model is not available.
    - An unexpected runtime error occurs during encoding.
    """


# ===========================================================================
# Model Loading
# ===========================================================================


def get_embedding_model():
    """
    Load and return the SentenceTransformer model as a module-level singleton.

    The model is loaded once on first call and cached for all subsequent calls.
    Reloading on every call would be prohibitively slow (seconds of startup time).

    Returns
    -------
    SentenceTransformer
        The cached model instance.

    Raises
    ------
    EmbeddingGenerationError
        If the model cannot be loaded (e.g. not installed, network unavailable).
    """
    global _MODEL_INSTANCE

    if _MODEL_INSTANCE is not None:
        return _MODEL_INSTANCE

    try:
        from sentence_transformers import SentenceTransformer  # type: ignore

        logger.info("Loading SentenceTransformer model: %s", _MODEL_NAME)
        _MODEL_INSTANCE = SentenceTransformer(_MODEL_NAME)
        logger.info("SentenceTransformer model loaded successfully.")
        return _MODEL_INSTANCE

    except ImportError as exc:
        raise EmbeddingGenerationError(
            "sentence-transformers is not installed. "
            "Run: pip install sentence-transformers"
        ) from exc

    except Exception as exc:
        raise EmbeddingGenerationError(
            f"Failed to load embedding model '{_MODEL_NAME}': {exc}"
        ) from exc


# ===========================================================================
# Embedding Generation
# ===========================================================================


def generate_embedding(text: str) -> list[float]:
    """
    Encode *text* into a dense embedding vector.

    Parameters
    ----------
    text : str
        The text to embed.  Must be non-empty after stripping whitespace.

    Returns
    -------
    list[float]
        A list of floats representing the embedding vector.

    Raises
    ------
    EmbeddingGenerationError
        - If *text* is empty or whitespace-only.
        - If the model is unavailable.
        - If any unexpected runtime error occurs during encoding.
    """
    if not isinstance(text, str) or not text.strip():
        raise EmbeddingGenerationError(
            "Cannot generate embedding for empty or whitespace-only text. "
            "Please provide a non-empty string."
        )

    try:
        model = get_embedding_model()
        # encode() returns a numpy array; convert to a plain Python list[float]
        # for easy JSON serialisation and storage.
        vector = model.encode(text.strip(), convert_to_numpy=True)
        return vector.tolist()

    except EmbeddingGenerationError:
        # Re-raise our own exception type unmodified.
        raise

    except Exception as exc:
        raise EmbeddingGenerationError(
            f"Unexpected error while generating embedding: {exc}"
        ) from exc


# ===========================================================================
# Similarity Computation
# ===========================================================================


def cosine_similarity_score(
    embedding_a: list[float],
    embedding_b: list[float],
) -> float:
    """
    Compute the cosine similarity between two embedding vectors and return a
    score in the range **0 – 100** (percentage similarity).

    The formula is ``max(0, cosine_similarity) * 100``:

    * **100** — identical (or perfectly aligned) vectors
    * **70–95** — semantically similar text (typical for matching resume/job pairs)
    * **10–30** — unrelated text in the same language
    * **0** — orthogonal or anti-correlated vectors (clamped to 0)

    Note: this is intentionally *not* the ``(raw+1)/2 * 100`` formula.
    That formula shifts orthogonal vectors to 50, making "unrelated" English
    sentences appear ~55–60% similar because any two English sentences tend
    to have a small positive raw cosine.  ``max(0, raw)*100`` gives an
    intuitive percentage-match scale.

    Parameters
    ----------
    embedding_a : list[float]
        First embedding vector.
    embedding_b : list[float]
        Second embedding vector.  Must have the same length as *embedding_a*.

    Returns
    -------
    float
        Cosine similarity scaled to [0, 100].
        Returns exactly 100.0 for two identical non-zero vectors.
        Returns 0.0 for orthogonal or anti-correlated vectors.

    Raises
    ------
    ValueError
        If either vector is empty or they have different lengths.
    """
    if not embedding_a or not embedding_b:
        raise ValueError("Embedding vectors must be non-empty.")

    a = np.array(embedding_a, dtype=np.float64)
    b = np.array(embedding_b, dtype=np.float64)

    if a.shape != b.shape:
        raise ValueError(
            f"Embedding length mismatch: {a.shape} vs {b.shape}."
        )

    # Cosine similarity = dot(a, b) / (||a|| * ||b||)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)

    if norm_a == 0.0 or norm_b == 0.0:
        # Zero-vector has undefined cosine similarity; treat as 0 similarity.
        return 0.0

    raw_similarity = np.dot(a, b) / (norm_a * norm_b)

    # Clamp to [-1, 1] to guard against floating-point rounding above 1.0
    raw_similarity = float(np.clip(raw_similarity, -1.0, 1.0))

    # Scale to [0, 100] as a percentage similarity:
    #   max(0, raw) * 100
    # This maps:
    #   1.0  → 100  (identical vectors)
    #   0.0  → 0    (orthogonal / no relation)
    #  <0    → 0    (anti-correlated; clamped to 0)
    #
    # This is intentionally NOT the (raw+1)/2 * 100 formula.
    # That formula shifts the midpoint to 50 and makes mildly positive
    # cosine values (e.g. 0.16 for any two English sentences) appear as
    # ~58% similar, which is misleading.  The max(0, raw)*100 formula
    # gives an intuitive "percentage match" where unrelated professional
    # sentences score ~10-30 and semantically close sentences score 70-95.
    score = max(0.0, raw_similarity) * 100.0

    return round(score, 4)


# ===========================================================================
# Get-or-Generate Pattern (for callers that persist embeddings)
# ===========================================================================


def get_or_generate_embedding(
    text: str,
    cached_embedding: Optional[list[float]],
    cached_text_hash: Optional[str] = None,
    current_text_hash: Optional[str] = None,
) -> tuple[list[float], bool]:
    """
    Return a cached embedding if the underlying text hasn't changed,
    otherwise generate a fresh one.

    This implements the performance requirement: avoid re-encoding the same
    text on every request by reusing persisted embeddings whenever the content
    fingerprint matches.

    Parameters
    ----------
    text : str
        The current text to embed.
    cached_embedding : list[float] | None
        Previously stored embedding (e.g. from Resume.embedding or Job.embedding).
    cached_text_hash : str | None
        The SHA-256 (or similar) fingerprint of the text that produced the
        cached embedding.  Pass None to always regenerate.
    current_text_hash : str | None
        The SHA-256 fingerprint of *text*.  Pass None to always regenerate.

    Returns
    -------
    (embedding, was_regenerated) : (list[float], bool)
        ``was_regenerated`` is True if a new embedding was generated, False
        if the cached one was reused.
    """
    # Reuse cached embedding if the hash matches and cache exists.
    if (
        cached_embedding is not None
        and cached_text_hash is not None
        and current_text_hash is not None
        and cached_text_hash == current_text_hash
    ):
        logger.debug("Embedding cache HIT: reusing cached vector (hash=%s)", cached_text_hash[:8])
        return cached_embedding, False

    logger.debug(
        "Embedding cache MISS: generating fresh vector (hash=%s)",
        (current_text_hash or "none")[:8],
    )
    # Generate a fresh embedding.
    embedding = generate_embedding(text)
    return embedding, True


def text_hash(text: str) -> str:
    """
    Return a compact SHA-256 hex fingerprint of *text*, used to detect
    whether the content has changed since the last embedding was stored.
    """
    import hashlib

    return hashlib.sha256(text.encode("utf-8")).hexdigest()
