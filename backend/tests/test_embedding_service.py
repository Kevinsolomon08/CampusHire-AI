# tests/test_embedding_service.py
# Comprehensive tests for app/ai/embedding_service.py.
#
# Tests verify:
#   1. Semantically similar sentences produce a high similarity score (> 60).
#   2. Clearly unrelated sentences produce a low similarity score (< 40).
#   3. Empty string raises EmbeddingGenerationError.
#   4. cosine_similarity_score returns a value in [0, 100].
#   5. Two identical embeddings produce a score of exactly 100.0.
#   6. get_or_generate_embedding caching logic.
#   7. text_hash determinism and uniqueness.
#   8. cosine_similarity_score handles zero vectors and length mismatch.

import hashlib
import pytest

from app.ai.embedding_service import (
    EmbeddingGenerationError,
    cosine_similarity_score,
    generate_embedding,
    get_embedding_model,
    get_or_generate_embedding,
    text_hash,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def model():
    """Load the embedding model once for the whole module."""
    return get_embedding_model()


@pytest.fixture(scope="module")
def similar_sentence_a():
    return "Developed REST APIs using Python and FastAPI"


@pytest.fixture(scope="module")
def similar_sentence_b():
    return "Looking for candidates experienced in Python backend development and RESTful APIs"


@pytest.fixture(scope="module")
def unrelated_sentence_a():
    return "Skilled chef with 10 years restaurant experience in fine dining and pastry arts"


@pytest.fixture(scope="module")
def unrelated_sentence_b():
    return "Senior Java backend engineer with Kubernetes experience and distributed systems"


@pytest.fixture(scope="module")
def emb_similar_a(similar_sentence_a):
    return generate_embedding(similar_sentence_a)


@pytest.fixture(scope="module")
def emb_similar_b(similar_sentence_b):
    return generate_embedding(similar_sentence_b)


@pytest.fixture(scope="module")
def emb_unrelated_a(unrelated_sentence_a):
    return generate_embedding(unrelated_sentence_a)


@pytest.fixture(scope="module")
def emb_unrelated_b(unrelated_sentence_b):
    return generate_embedding(unrelated_sentence_b)


# ---------------------------------------------------------------------------
# 1 — Model Loading
# ---------------------------------------------------------------------------

class TestModelLoading:
    def test_model_loads_without_error(self, model):
        assert model is not None

    def test_model_is_singleton(self):
        """Calling get_embedding_model() twice must return the exact same object."""
        m1 = get_embedding_model()
        m2 = get_embedding_model()
        assert m1 is m2


# ---------------------------------------------------------------------------
# 2 — generate_embedding
# ---------------------------------------------------------------------------

class TestGenerateEmbedding:
    def test_returns_list(self, emb_similar_a):
        assert isinstance(emb_similar_a, list)

    def test_vector_is_non_empty(self, emb_similar_a):
        assert len(emb_similar_a) > 0

    def test_all_elements_are_floats(self, emb_similar_a):
        assert all(isinstance(x, float) for x in emb_similar_a)

    def test_empty_string_raises_error(self):
        with pytest.raises(EmbeddingGenerationError):
            generate_embedding("")

    def test_whitespace_only_raises_error(self):
        with pytest.raises(EmbeddingGenerationError):
            generate_embedding("   \n\t  ")

    def test_different_texts_produce_different_vectors(self, emb_similar_a, emb_unrelated_b):
        assert emb_similar_a != emb_unrelated_b

    def test_same_text_produces_same_vector(self):
        text = "Python FastAPI developer"
        v1 = generate_embedding(text)
        v2 = generate_embedding(text)
        assert v1 == v2

    def test_vector_dimensionality_is_consistent(self, emb_similar_a, emb_similar_b):
        assert len(emb_similar_a) == len(emb_similar_b)


# ---------------------------------------------------------------------------
# 3 — cosine_similarity_score
# ---------------------------------------------------------------------------

class TestCosineSimilarityScore:
    def test_returns_float(self, emb_similar_a, emb_similar_b):
        score = cosine_similarity_score(emb_similar_a, emb_similar_b)
        assert isinstance(score, float)

    def test_score_in_range_0_to_100(self, emb_similar_a, emb_unrelated_b):
        score = cosine_similarity_score(emb_similar_a, emb_unrelated_b)
        assert 0.0 <= score <= 100.0

    def test_identical_embeddings_return_100(self, emb_similar_a):
        score = cosine_similarity_score(emb_similar_a, emb_similar_a)
        assert score == pytest.approx(100.0, abs=0.01)

    def test_length_mismatch_raises_value_error(self, emb_similar_a):
        short_vec = emb_similar_a[:10]
        with pytest.raises(ValueError, match="length mismatch"):
            cosine_similarity_score(emb_similar_a, short_vec)

    def test_empty_vectors_raise_value_error(self):
        with pytest.raises(ValueError):
            cosine_similarity_score([], [])

    def test_all_valid_pairs_stay_in_range(
        self, emb_similar_a, emb_similar_b, emb_unrelated_a, emb_unrelated_b
    ):
        pairs = [
            (emb_similar_a, emb_similar_b),
            (emb_unrelated_a, emb_unrelated_b),
            (emb_similar_a, emb_unrelated_a),
            (emb_similar_b, emb_unrelated_b),
        ]
        for a, b in pairs:
            score = cosine_similarity_score(a, b)
            assert 0.0 <= score <= 100.0, (
                f"Score {score} out of range for pair"
            )


# ---------------------------------------------------------------------------
# 4 — Semantic Discrimination (the core quality assertions)
# ---------------------------------------------------------------------------

class TestSemanticDiscrimination:
    def test_similar_sentences_produce_high_score(self, emb_similar_a, emb_similar_b):
        """
        'Developed REST APIs using Python and FastAPI' vs
        'Looking for candidates experienced in Python backend development and RESTful APIs'
        should have meaningfully high similarity (> 60 / 100).
        """
        score = cosine_similarity_score(emb_similar_a, emb_similar_b)
        assert score > 60, (
            f"Expected similar sentences to score > 60, got {score:.2f}. "
            "The model may not be distinguishing semantically related content correctly."
        )

    def test_unrelated_sentences_produce_low_score(self, emb_unrelated_a, emb_unrelated_b):
        """
        'Skilled chef with 10 years restaurant experience' vs
        'Senior Java backend engineer with Kubernetes experience'
        should have low similarity (< 40 / 100).
        """
        score = cosine_similarity_score(emb_unrelated_a, emb_unrelated_b)
        assert score < 40, (
            f"Expected unrelated sentences to score < 40, got {score:.2f}. "
            "The model may be producing overly similar embeddings for unrelated content."
        )

    def test_similar_scores_higher_than_unrelated(
        self, emb_similar_a, emb_similar_b, emb_unrelated_a, emb_unrelated_b
    ):
        """Similar pair must clearly outscore the unrelated pair."""
        similar_score = cosine_similarity_score(emb_similar_a, emb_similar_b)
        unrelated_score = cosine_similarity_score(emb_unrelated_a, emb_unrelated_b)
        assert similar_score > unrelated_score, (
            f"Similar score ({similar_score:.2f}) should exceed "
            f"unrelated score ({unrelated_score:.2f})."
        )

    def test_job_resume_pair_is_meaningfully_similar(self):
        """
        A resume snippet that closely matches a job description should produce
        a high match score — the core use case for campus hiring.
        """
        resume_text = (
            "Experienced Python developer with 2 years building FastAPI microservices, "
            "REST APIs, PostgreSQL, and Docker deployments."
        )
        job_text = (
            "We are looking for a backend Python engineer experienced with FastAPI, "
            "REST API design, relational databases, and containerisation with Docker."
        )
        emb_resume = generate_embedding(resume_text)
        emb_job = generate_embedding(job_text)
        score = cosine_similarity_score(emb_resume, emb_job)
        assert score > 70, (
            f"Expected a closely matching resume-job pair to score > 70, got {score:.2f}."
        )


# ---------------------------------------------------------------------------
# 5 — get_or_generate_embedding caching
# ---------------------------------------------------------------------------

class TestGetOrGenerateEmbedding:
    def test_returns_cached_when_hash_matches(self):
        text = "Python developer"
        existing_emb = generate_embedding(text)
        h = text_hash(text)

        result_emb, was_regenerated = get_or_generate_embedding(
            text=text,
            cached_embedding=existing_emb,
            cached_text_hash=h,
            current_text_hash=h,
        )
        assert result_emb is existing_emb
        assert was_regenerated is False

    def test_regenerates_when_hash_mismatches(self):
        old_text = "Python developer"
        new_text = "Java developer with Spring Boot expertise"
        old_emb = generate_embedding(old_text)
        old_hash = text_hash(old_text)
        new_hash = text_hash(new_text)

        result_emb, was_regenerated = get_or_generate_embedding(
            text=new_text,
            cached_embedding=old_emb,
            cached_text_hash=old_hash,
            current_text_hash=new_hash,
        )
        assert was_regenerated is True
        assert result_emb != old_emb

    def test_regenerates_when_no_cache(self):
        text = "React frontend developer"
        result_emb, was_regenerated = get_or_generate_embedding(
            text=text,
            cached_embedding=None,
            cached_text_hash=None,
            current_text_hash=text_hash(text),
        )
        assert was_regenerated is True
        assert isinstance(result_emb, list)
        assert len(result_emb) > 0

    def test_regenerates_when_hash_not_provided(self):
        text = "DevOps engineer"
        existing_emb = generate_embedding(text)

        result_emb, was_regenerated = get_or_generate_embedding(
            text=text,
            cached_embedding=existing_emb,
            cached_text_hash=None,    # No hash stored
            current_text_hash=None,   # No hash computed
        )
        assert was_regenerated is True


# ---------------------------------------------------------------------------
# 6 — text_hash utility
# ---------------------------------------------------------------------------

class TestTextHash:
    def test_is_deterministic(self):
        t = "Consistent input text"
        assert text_hash(t) == text_hash(t)

    def test_same_as_manual_sha256(self):
        t = "Hello, CampusHire!"
        expected = hashlib.sha256(t.encode("utf-8")).hexdigest()
        assert text_hash(t) == expected

    def test_different_texts_produce_different_hashes(self):
        assert text_hash("Python developer") != text_hash("Java developer")

    def test_returns_64_char_hex_string(self):
        h = text_hash("test")
        assert len(h) == 64
        assert all(c in "0123456789abcdef" for c in h)
