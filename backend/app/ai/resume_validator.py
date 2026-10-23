"""
app/ai/resume_validator.py
==========================
Rule/heuristic-based resume content validator for CampusHire.

Determines whether a PDF extracted text actually looks like a resume,
as opposed to an invoice, receipt, research paper, legal document, article, etc.

Public API
----------
validate_resume_text(text: str, page_count: int | None = None) -> dict
    Returns::

        {
            "is_resume": bool,
            "score": float,         # 0.0 - 10.0
            "reasons": list[str],   # human-readable explanation bullets
        }
"""

from __future__ import annotations

import re
from typing import Any

from app.ai.resume_parser import _SECTION_RE, _SKILL_LOWER

# ---------------------------------------------------------------------------
# Negative-signal keyword sets
# ---------------------------------------------------------------------------

_INVOICE_TERMS: frozenset = frozenset([
    "invoice", "bill to", "subtotal", "total amount", "amount due",
    "payment due", "tax invoice", "gst", "vat", "receipt",
    "transaction id", "order number", "item description", "unit price", "quantity",
])

_RESEARCH_TERMS: frozenset = frozenset([
    "abstract", "keywords:", "methodology", "conclusion", "references",
    "bibliography", "doi:", "ieee", "journal of", "proceedings of",
    "et al.", "fig.", "table 1", "literature review",
])

_LEGAL_TERMS: frozenset = frozenset([
    "whereas", "hereinafter", "indemnification", "liability",
    "jurisdiction", "governing law", "force majeure", "plaintiff",
    "defendant", "affidavit", "notary", "pursuant to",
    "articles of", "by-laws",
])

_ARTICLE_TERMS: frozenset = frozenset([
    "published on", "reporter", "staff writer", "editorial board",
    "subscribe", "advertisement", "breaking news", "read more",
    "share this", "comments",
])

_NEGATIVE_SIGNALS: list = [
    (_INVOICE_TERMS,  "invoice/receipt",  2.0),
    (_RESEARCH_TERMS, "research paper",   1.5),
    (_LEGAL_TERMS,    "legal document",   2.0),
    (_ARTICLE_TERMS,  "article/news",     1.5),
]

# ---------------------------------------------------------------------------
# Positive signal patterns
# ---------------------------------------------------------------------------

_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)
_PHONE_RE = re.compile(
    r"(?:\+\d{1,3}[\s\-.]?)?\(?\d{3,5}\)?[\s\-.]?\d{3,5}[\s\-.]?\d{4,5}"
)
_URL_RE = re.compile(
    r"(?:linkedin\.com|github\.com|https?://[^\s]{8,})",
    re.IGNORECASE,
)
_ACTION_VERBS_RE = re.compile(
    r"\b(?:developed|implemented|designed|built|managed|led|optimized|deployed|"
    r"created|maintained|collaborated|delivered|achieved|improved|analysed|"
    r"analyzed|researched|coordinated|resolved|configured|automated|mentored|"
    r"engineered|architected|integrated|migrated|scaled|reduced|increased)\b",
    re.IGNORECASE,
)
_DEGREE_RE = re.compile(
    r"\b(?:B\.?Tech|B\.?E\.?|B\.?Sc|M\.?Tech|MBA|MCA|BCA|Ph\.?D|"
    r"Bachelor|Master|Diploma|Associate|Doctor(?:ate)?)\b",
    re.IGNORECASE,
)
_NAME_LIKE_RE = re.compile(
    r"^[A-Z][a-z]+ [A-Z][a-z]+",
    re.MULTILINE,
)

# Scoring weights
_WEIGHT_SECTION_MATCH   = 1.0
_WEIGHT_SKILL_MATCH     = 1.5
_WEIGHT_CONTACT_INFO    = 1.0
_WEIGHT_LINKEDIN_GITHUB = 0.5
_WEIGHT_ACTION_VERBS    = 1.0
_WEIGHT_DEGREE          = 1.0
_WEIGHT_NAME_LIKE       = 0.5
_MAX_POSITIVE           = 10.0
_MIN_CHARS              = 100


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_resume_text(
    text: str,
    page_count: int | None = None,
) -> dict[str, Any]:
    """
    Assess whether *text* looks like a resume.

    Parameters
    ----------
    text : str
        Plain text extracted from the PDF.
    page_count : int | None
        Number of PDF pages (optional).

    Returns
    -------
    dict with keys: is_resume (bool), score (float), reasons (list[str]).
    """
    reasons: list[str] = []
    score: float = 0.0
    text_lower = text.lower()

    # 0. Must have enough text
    char_count = len(text.replace(" ", "").replace("\n", ""))
    if char_count < _MIN_CHARS:
        return {
            "is_resume": False,
            "score": 0.0,
            "reasons": ["Document contains too little text to evaluate."],
        }

    # 1a. Resume section headers
    matched_sections: list[str] = []
    for section_name, pattern in _SECTION_RE.items():
        if pattern.search(text):
            matched_sections.append(section_name)

    section_pts = min(len(matched_sections), 4) * _WEIGHT_SECTION_MATCH
    score += section_pts
    if matched_sections:
        reasons.append(
            "Contains {} recognised resume section(s): {} (+{:.1f} pts).".format(
                len(matched_sections), ", ".join(matched_sections), section_pts
            )
        )
    else:
        reasons.append(
            "No standard resume section headers detected "
            "(skills, education, experience, etc.)."
        )

    # 1b. Technical skill keywords
    skill_hits: list[str] = []
    for lower_kw, canonical in _SKILL_LOWER.items():
        pat = r"(?<![a-zA-Z0-9])" + re.escape(lower_kw) + r"(?![a-zA-Z0-9])"
        if re.search(pat, text_lower):
            skill_hits.append(canonical)
            if len(skill_hits) >= 5:
                break

    if len(skill_hits) >= 2:
        score += _WEIGHT_SKILL_MATCH
        reasons.append(
            "Found {} technical skill keyword(s) (e.g. {}) (+{:.1f} pts).".format(
                len(skill_hits), ", ".join(skill_hits[:3]), _WEIGHT_SKILL_MATCH
            )
        )
    else:
        reasons.append(
            "Only {} known technical skill keyword(s) found.".format(len(skill_hits))
        )

    # 1c. Contact information
    has_email = bool(_EMAIL_RE.search(text))
    has_phone = bool(_PHONE_RE.search(text))
    if has_email or has_phone:
        score += _WEIGHT_CONTACT_INFO
        signals = []
        if has_email:
            signals.append("email")
        if has_phone:
            signals.append("phone number")
        reasons.append(
            "Contact information present ({}) (+{:.1f} pts).".format(
                ", ".join(signals), _WEIGHT_CONTACT_INFO
            )
        )
    else:
        reasons.append("No email address or phone number found.")

    # 1d. LinkedIn or GitHub URL
    if _URL_RE.search(text):
        score += _WEIGHT_LINKEDIN_GITHUB
        reasons.append(
            "Professional/portfolio URL (LinkedIn/GitHub) found (+{:.1f} pts).".format(
                _WEIGHT_LINKEDIN_GITHUB
            )
        )

    # 1e. Action verbs
    action_hits = _ACTION_VERBS_RE.findall(text)
    if len(action_hits) >= 3:
        score += _WEIGHT_ACTION_VERBS
        reasons.append(
            "Contains {} experience-style action verbs (+{:.1f} pts).".format(
                len(action_hits), _WEIGHT_ACTION_VERBS
            )
        )
    else:
        reasons.append(
            "Only {} experience-style action verb(s) found.".format(len(action_hits))
        )

    # 1f. Degree keywords
    if _DEGREE_RE.search(text):
        score += _WEIGHT_DEGREE
        reasons.append(
            "Degree qualification keyword found (+{:.1f} pts).".format(_WEIGHT_DEGREE)
        )
    else:
        reasons.append("No degree/qualification keyword found.")

    # 1g. Name-like sequence near the top
    header = text[:600]
    if _NAME_LIKE_RE.search(header):
        score += _WEIGHT_NAME_LIKE
        reasons.append(
            "Person-name-like text found near the document header (+{:.1f} pts).".format(
                _WEIGHT_NAME_LIKE
            )
        )

    # 2. Negative signals
    negative_categories_hit: list[str] = []
    for term_set, category_label, penalty in _NEGATIVE_SIGNALS:
        hits = [t for t in term_set if t in text_lower]
        if len(hits) >= 2:
            score -= penalty
            negative_categories_hit.append(
                "{} (matched: {}; -{:.1f} pts)".format(
                    category_label, ", ".join(hits[:3]), penalty
                )
            )

    if negative_categories_hit:
        reasons.append(
            "Negative signals found suggesting this is NOT a resume: {}.".format(
                "; ".join(negative_categories_hit)
            )
        )

    # 2b. Excessive page count
    if page_count is not None and page_count > 6:
        score -= 1.5
        reasons.append(
            "Document is {} pages long — unusually long for a resume (-1.5 pts).".format(
                page_count
            )
        )

    # 3. Clamp score
    score = max(0.0, min(_MAX_POSITIVE, score))

    # Import threshold lazily to avoid circular imports at module load
    from app.core.config import settings  # noqa: PLC0415

    min_score: float = float(getattr(settings, "RESUME_VALIDATION_MIN_SCORE", 6.0))
    is_resume = score >= min_score

    if is_resume:
        reasons.append(
            "Final score {:.1f}/{:.0f} — document accepted as a resume "
            "(threshold: {:.0f}).".format(score, _MAX_POSITIVE, min_score)
        )
    else:
        reasons.append(
            "Final score {:.1f}/{:.0f} — document rejected "
            "(minimum required: {:.0f}).".format(score, _MAX_POSITIVE, min_score)
        )

    return {
        "is_resume": is_resume,
        "score": round(score, 2),
        "reasons": reasons,
    }
