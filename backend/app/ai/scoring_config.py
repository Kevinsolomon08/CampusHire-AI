"""
app/ai/scoring_config.py
========================
Configuration constants and weights for CampusHire's AI applicant scoring engine.

Weights:
  - SEMANTIC_WEIGHT   : 0.50 (Cosine similarity of embeddings between job and resume)
  - SKILL_WEIGHT      : 0.25 (Matching required and preferred skills)
  - EXPERIENCE_WEIGHT : 0.15 (Relevance and duration of candidate experience vs job requirement)
  - EDUCATION_WEIGHT  : 0.10 (Alignment of degree/department with job profile)

Invariant:
  The four weights must sum to exactly 1.0.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Scoring Component Weights (Central configuration, not hardcoded inline)
# ---------------------------------------------------------------------------
SEMANTIC_WEIGHT: float = 0.50
SKILL_WEIGHT: float = 0.25
EXPERIENCE_WEIGHT: float = 0.15
EDUCATION_WEIGHT: float = 0.10

# Multiplier for skill match weighting (required matches count double)
REQUIRED_SKILL_WEIGHT_MULTIPLIER: float = 2.0
PREFERRED_SKILL_WEIGHT_MULTIPLIER: float = 1.0

# ---------------------------------------------------------------------------
# Invariant check: Weights must sum to exactly 1.0
# ---------------------------------------------------------------------------
TOTAL_WEIGHT: float = SEMANTIC_WEIGHT + SKILL_WEIGHT + EXPERIENCE_WEIGHT + EDUCATION_WEIGHT
assert abs(TOTAL_WEIGHT - 1.0) < 1e-9, (
    f"Scoring weights must sum to 1.0, got {TOTAL_WEIGHT:.4f} "
    f"(SEMANTIC={SEMANTIC_WEIGHT}, SKILL={SKILL_WEIGHT}, "
    f"EXPERIENCE={EXPERIENCE_WEIGHT}, EDUCATION={EDUCATION_WEIGHT})"
)
