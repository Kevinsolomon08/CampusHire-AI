"""
tests/test_resume_validator.py
==============================
Unit tests for app/ai/resume_validator.py.

All tests operate on synthetic inline text — no real PDFs are needed.
"""

from __future__ import annotations

import pytest

from app.ai.resume_validator import validate_resume_text


# ---------------------------------------------------------------------------
# Synthetic samples
# ---------------------------------------------------------------------------

STRONG_RESUME = """
Priya Sharma
priya.sharma@email.com | +91 9876543210 | github.com/priyasharma

Education
B.Tech in Computer Science
XYZ Institute of Technology, Hyderabad | 2020 - 2024
CGPA: 8.7/10

Skills
Python, Django, React, PostgreSQL, Docker, AWS, Git, Machine Learning, NumPy, Pandas

Experience
Software Developer Intern
ABC Technologies, Hyderabad | June 2023 - August 2023
- Developed RESTful APIs using Python and Django
- Deployed containerised services using Docker on AWS
- Improved query performance by 30 percent with PostgreSQL optimisations

Projects
Student Management Portal
A web application to manage student records using Django and React.
Technologies: Python, Django, React, PostgreSQL, Docker

Certifications
AWS Certified Cloud Practitioner - Amazon AWS
Machine Learning Specialisation - Coursera
""".strip()


MINIMAL_RESUME = """
John Doe
john@example.com
+91 9876543210

Skills
Python, JavaScript, React

Education
B.Sc Computer Science
State University | 2019 - 2023
""".strip()


INVOICE_TEXT = """
INVOICE #INV-2024-001

Bill To:
Acme Corporation
123 Business Street
City, Country

Item Description          Quantity    Unit Price    Total
Software License           1          $500.00       $500.00
Support Services           5          $100.00       $500.00

Subtotal:    $1,000.00
Tax (GST):   $180.00
Total Amount Due:  $1,180.00

Payment Due: 2024-01-30
Transaction ID: TXN-987654321

Thank you for your business.
""".strip()


RESEARCH_PAPER = """
Abstract

This paper presents a novel methodology for distributed systems optimisation.
We propose an algorithm based on consistent hashing and present empirical results.

Keywords: distributed systems, consistency, hashing

Introduction
Distributed systems have become an integral part of modern infrastructure.

Methodology
We conducted experiments on a cluster of 10 nodes.

Conclusion
Our methodology reduces latency by 40 percent compared to existing approaches.

References
[1] Lamport, L. et al. (2001). Paxos made simple. DOI: 10.1145/12345
[2] DeCandia et al. (2007). Dynamo. Proceedings of SOSP.
""".strip()


LEGAL_DOCUMENT = """
SERVICE AGREEMENT

This Agreement is entered into as of January 1, 2024, between Party A and Party B.

WHEREAS, Party A desires to engage Party B for certain services;
WHEREAS, Party B is willing to provide such services;

Hereinafter "Service Provider" shall mean Party B.

Governing Law
This Agreement shall be governed by and construed pursuant to the laws of the State.

Force Majeure
Neither party shall be liable for any delay due to causes beyond their control.

Indemnification
Party B agrees to indemnify, defend, and hold harmless Party A from any liability.

IN WITNESS WHEREOF, the parties have executed this Agreement.
""".strip()


EMPTY_TEXT = "   \n  \n  "
SHORT_TEXT = "Hello world. This is short."


# ---------------------------------------------------------------------------
# Tests — documents that SHOULD be accepted
# ---------------------------------------------------------------------------

class TestResumeAccepted:
    def test_strong_resume_is_accepted(self):
        result = validate_resume_text(STRONG_RESUME)
        assert result["is_resume"] is True
        assert result["score"] >= 6.0

    def test_strong_resume_has_reasons(self):
        result = validate_resume_text(STRONG_RESUME)
        assert isinstance(result["reasons"], list)
        assert len(result["reasons"]) > 0

    def test_strong_resume_detects_sections(self):
        result = validate_resume_text(STRONG_RESUME)
        reasons_text = " ".join(result["reasons"])
        # Should mention at least one section
        assert any(
            sec in reasons_text
            for sec in ("skills", "education", "experience", "projects", "certifications")
        )

    def test_minimal_resume_is_accepted(self):
        result = validate_resume_text(MINIMAL_RESUME)
        assert result["is_resume"] is True

    def test_resume_with_page_count_hint(self):
        result = validate_resume_text(STRONG_RESUME, page_count=2)
        assert result["is_resume"] is True

    def test_score_is_float(self):
        result = validate_resume_text(STRONG_RESUME)
        assert isinstance(result["score"], float)

    def test_score_within_bounds(self):
        result = validate_resume_text(STRONG_RESUME)
        assert 0.0 <= result["score"] <= 10.0


# ---------------------------------------------------------------------------
# Tests — documents that SHOULD be rejected
# ---------------------------------------------------------------------------

class TestResumeRejected:
    def test_invoice_is_rejected(self):
        result = validate_resume_text(INVOICE_TEXT)
        assert result["is_resume"] is False

    def test_invoice_score_below_threshold(self):
        result = validate_resume_text(INVOICE_TEXT)
        assert result["score"] < 6.0

    def test_invoice_mentions_negative_signal(self):
        result = validate_resume_text(INVOICE_TEXT)
        reasons_text = " ".join(result["reasons"]).lower()
        assert "invoice" in reasons_text or "negative" in reasons_text

    def test_research_paper_is_rejected(self):
        result = validate_resume_text(RESEARCH_PAPER)
        assert result["is_resume"] is False

    def test_legal_document_is_rejected(self):
        result = validate_resume_text(LEGAL_DOCUMENT)
        assert result["is_resume"] is False

    def test_empty_text_is_rejected(self):
        result = validate_resume_text(EMPTY_TEXT)
        assert result["is_resume"] is False
        assert result["score"] == 0.0

    def test_very_short_text_is_rejected(self):
        result = validate_resume_text(SHORT_TEXT)
        assert result["is_resume"] is False


# ---------------------------------------------------------------------------
# Tests — edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_page_count_too_high_penalises_score(self):
        result_normal = validate_resume_text(STRONG_RESUME, page_count=2)
        result_long   = validate_resume_text(STRONG_RESUME, page_count=10)
        # Score should be lower for long document
        assert result_long["score"] <= result_normal["score"]

    def test_return_structure_always_present(self):
        for text in [STRONG_RESUME, INVOICE_TEXT, EMPTY_TEXT]:
            result = validate_resume_text(text)
            assert "is_resume" in result
            assert "score" in result
            assert "reasons" in result

    def test_is_resume_is_bool(self):
        for text in [STRONG_RESUME, INVOICE_TEXT]:
            result = validate_resume_text(text)
            assert isinstance(result["is_resume"], bool)

    def test_reasons_is_list_of_strings(self):
        result = validate_resume_text(STRONG_RESUME)
        assert all(isinstance(r, str) for r in result["reasons"])
