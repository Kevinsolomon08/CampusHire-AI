from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from app.core.config import settings

_ACCEPTED_LABELS = (
    "CGPA",
    "C.G.P.A",
    "CPI",
    "OGPA",
    "cumulative grade point average",
    "cumulative GPA",
    "overall GPA",
    "overall grade point average",
    "final CGPA",
)

_RESTRICTED_LABELS = (
    "SGPA",
    "SPI",
    "TGPA",
    "semester GPA",
    "term GPA",
    "GPA",
)


def _normalize_text(text: str) -> str:
    cleaned = unicodedata.normalize("NFC", text or "")
    cleaned = "".join(ch for ch in cleaned if ch.isprintable() or ch in "\n\t\r")
    return cleaned.strip()


def _document_score(text: str) -> float:
    clean = _normalize_text(text).lower()
    score = 0.0
    if re.search(r"\b(grade|gradesheet|marksheet|semester|cgpa|gpa|credit|grade point|cumulative)\b", clean):
        score += 3.0
    if re.search(r"\b(cgpa|cpi|ogpa|cumulative grade point average|overall gpa)\b", clean):
        score += 4.0
    if re.search(r"\b\d+(?:\.\d{1,3})?\b", clean):
        score += 2.0
    if re.search(r"\b(credits|grade points|result|passed|failed)\b", clean):
        score += 1.5
    return min(score, 10.0)


def validate_marksheet_text(text: str, page_count: int | None = None):
    """Return a validation payload for a marksheet PDF's extracted text."""
    normalized = _normalize_text(text)
    clean_len = len(re.sub(r"\s+", "", normalized))

    reasons: list[str] = []
    if clean_len < 50:
        reasons.append(
            "We couldn't read text from this PDF. Please upload the digital (text-based) marksheet PDF from your university portal."
        )
        return {"is_valid": False, "score": 0.0, "reasons": reasons, "error_code": "SCANNED_MARKSHEET"}

    if page_count is not None and page_count > 10:
        reasons.append("Marksheets longer than 10 pages are not supported.")
        return {"is_valid": False, "score": _document_score(normalized), "reasons": reasons, "error_code": "MARKSHEET_TOO_LONG"}

    score = _document_score(normalized)
    if not re.search(r"\b(semester|marksheet|gradesheet|grade point|credit|cgpa|gpa|cpi|ogpa)\b", normalized, re.IGNORECASE):
        reasons.append("This PDF does not look like an academic marksheet.")

    final_score = float(score)
    is_valid = len(reasons) == 0 and final_score >= float(settings.MARKSHEET_VALIDATION_MIN_SCORE)
    if not is_valid and reasons == []:
        reasons.append("This document does not satisfy the minimum marksheet validation score.")

    return {
        "is_valid": is_valid,
        "score": final_score,
        "reasons": reasons,
        "error_code": None if is_valid else "NOT_A_MARKSHEET",
    }


def _find_label_candidates(text: str):
    normalized = _normalize_text(text)
    lines = [line.strip() for line in normalized.splitlines() if line.strip()]
    candidates: list[dict[str, Any]] = []

    label_re = re.compile(
        r"(?:CGPA|C\.G\.P\.A|CPI|OGPA|cumulative\s+grade\s+point\s+average|cumulative\s+GPA|overall\s+GPA|overall\s+grade\s+point\s+average|final\s+CGPA)",
        re.IGNORECASE,
    )
    for idx, line in enumerate(lines):
        if not label_re.search(line):
            continue
        if re.search(r"\b(?:SGPA|SPI|TGPA|semester\s+GPA|term\s+GPA)\b", line, re.IGNORECASE):
            continue

        matches = re.findall(r"\b\d{1,2}(?:\.\d{1,3})?\b", line)
        if matches:
            for value in matches:
                candidates.append({"value": value, "label": line, "line_index": idx, "same_line": True})
            continue

        next_line = lines[idx + 1] if idx + 1 < len(lines) else ""
        next_matches = re.findall(r"\b\d{1,2}(?:\.\d{1,3})?\b", next_line)
        if next_matches:
            candidates.extend({"value": value, "label": line, "line_index": idx, "same_line": False} for value in next_matches)

    text_matcher = re.finditer(
        r"(?P<label>(?:CGPA|C\.G\.P\.A|CPI|OGPA|cumulative\s+grade\s+point\s+average|cumulative\s+GPA|overall\s+GPA|overall\s+grade\s+point\s+average|final\s+CGPA))(?:\s*[:=\-]\s*|\s+)?(?P<value>\d{1,2}(?:\.\d{1,3})?)(?:\s*(?:/\s*10(?:\.0)?|/\s*4(?:\.0)?|/\s*5(?:\.0)?)?\s*)?",
        normalized,
        re.IGNORECASE,
    )
    for match in text_matcher:
        label = match.group("label")
        value = match.group("value")
        if re.search(r"\b(?:SGPA|SPI|TGPA|semester\s+GPA|term\s+GPA)\b", label, re.IGNORECASE):
            continue
        candidates.append({"value": value, "label": label, "line_index": -1, "same_line": True})

    deduped: list[dict[str, Any]] = []
    seen = set()
    for item in candidates:
        key = (item["value"], item["label"].lower().strip())
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)
    return deduped


def extract_cgpa(text: str):
    """Extract cumulative CGPA from marksheet text, returning a structured result."""
    normalized = _normalize_text(text)
    if not normalized:
        return {
            "cgpa": None,
            "label": None,
            "confidence": None,
            "candidates": [],
            "error_code": "CGPA_NOT_FOUND",
            "message": "No cumulative CGPA could be extracted from this marksheet.",
        }

    raw_candidates: list[dict[str, Any]] = []
    for item in _find_label_candidates(normalized):
        raw_value = item["value"]
        try:
            value_decimal = Decimal(raw_value)
        except InvalidOperation:
            continue
        label = item["label"]
        raw_label = label.strip()
        lower_label = raw_label.lower()
        is_final = any(token in lower_label for token in ("final", "overall", "cumulative"))
        raw_candidates.append({
            "value": value_decimal,
            "label": raw_label,
            "final": is_final,
            "scale": "10",
            "raw": raw_value,
        })

    if not raw_candidates:
        if re.search(r"\b(?:SGPA|SPI|TGPA|semester\s+GPA|term\s+GPA)\b", normalized, re.IGNORECASE):
            return {
                "cgpa": None,
                "label": None,
                "confidence": None,
                "candidates": [],
                "error_code": "SGPA_ONLY",
                "message": "Please upload a cumulative marksheet or the latest semester sheet that explicitly shows the CGPA.",
            }
        return {
            "cgpa": None,
            "label": None,
            "confidence": None,
            "candidates": [],
            "error_code": "CGPA_NOT_FOUND",
            "message": "No recognized cumulative CGPA label and value were found in the marksheet.",
        }

    # Exclude semester-only values when no cumulative label exists.
    if not any(c["final"] for c in raw_candidates):
        if re.search(r"\b(?:SGPA|SPI|TGPA|semester\s+GPA|term\s+GPA)\b", normalized, re.IGNORECASE):
            return {
                "cgpa": None,
                "label": None,
                "confidence": None,
                "candidates": [c["raw"] for c in raw_candidates],
                "error_code": "SGPA_ONLY",
                "message": "Please upload a cumulative marksheet or the latest semester sheet that explicitly shows the CGPA.",
            }

    unique_by_value = []
    seen_values = set()
    for candidate in raw_candidates:
        key = str(candidate["value"])
        if key in seen_values:
            continue
        seen_values.add(key)
        unique_by_value.append(candidate)

    # Reject unsupported scales that are explicitly mentioned
    for candidate in unique_by_value:
        if re.search(r"/(?:4|4\.0|5|5\.0)\b|\b(?:4\.0|5\.0)\s*scale\b", normalized, re.IGNORECASE):
            return {
                "cgpa": None,
                "label": candidate["label"],
                "confidence": None,
                "candidates": [c["raw"] for c in unique_by_value],
                "error_code": "UNSUPPORTED_SCALE",
                "message": "This marksheet uses an unsupported CGPA scale. Upload a 10-point cumulative score.",
            }

    finals = [candidate for candidate in unique_by_value if candidate["final"]]
    if finals:
        selected = finals[0]
    elif len(unique_by_value) == 1:
        selected = unique_by_value[0]
    elif len({str(c["value"]) for c in unique_by_value}) == 1:
        selected = unique_by_value[0]
    else:
        return {
            "cgpa": None,
            "label": None,
            "confidence": None,
            "candidates": [c["raw"] for c in unique_by_value],
            "error_code": "CGPA_AMBIGUOUS",
            "message": "Multiple different CGPA candidates were found without a clear final cumulative value.",
        }

    value = selected["value"]
    if value < Decimal("0") or value > Decimal("10"):
        return {
            "cgpa": None,
            "label": selected["label"],
            "confidence": "HIGH" if selected["final"] else "MEDIUM",
            "candidates": [c["raw"] for c in unique_by_value],
            "error_code": "CGPA_OUT_OF_RANGE",
            "message": "The extracted CGPA is outside the supported 0-10 range.",
        }

    normalized_value = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return {
        "cgpa": normalized_value,
        "label": selected["label"],
        "confidence": "HIGH" if selected["final"] or "CGPA" in selected["label"].upper() else "MEDIUM",
        "candidates": [c["raw"] for c in unique_by_value],
        "error_code": None,
        "message": "Cumulative CGPA extracted successfully.",
    }
