"""
tests/test_resume_parser.py
===========================
Pytest tests for app/ai/resume_parser.py.

Synthetic resume texts are constructed inline — no real PDF files required.
The extract_text_from_pdf tests mock pdfplumber at the text level so the
suite runs without any actual PDF on disk.
"""

from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

from app.ai.resume_parser import (
    extract_text_from_pdf,
    parse_resume,
    ResumeExtractionError,
    ResumeParsingError,
)


# ===========================================================================
# Synthetic resume samples
# ===========================================================================

# Sample A — Well-formatted, all sections present, skills as comma-separated list
RESUME_A = """
Priya Sharma
priya.sharma@email.com | +91 9876543210 | LinkedIn: linkedin.com/in/priyasharma

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
- Deployed containerized services using Docker on AWS
- Improved query performance by 30% with PostgreSQL optimizations

Projects
Student Management Portal
A web application to manage student records using Django and React.
Technologies: Python, Django, React, PostgreSQL, Docker

Certifications
AWS Certified Cloud Practitioner - Amazon AWS
Machine Learning Specialization - Coursera
""".strip()


# Sample B — Variant section names ("WORK EXPERIENCE"), skills as bullet points
RESUME_B = """
Rahul Kumar
rahul.kumar@techmail.com
Phone: 8765432109

EDUCATION
Bachelor of Engineering in Information Technology
National College of Engineering | 2019 - 2023
GPA: 7.9

TECHNICAL SKILLS
- JavaScript
- Node.js
- MongoDB
- Express
- React.js
- Git
- Linux
- Docker

WORK EXPERIENCE

Frontend Developer Intern
WebCraft Solutions, Bangalore | Jan 2023 - May 2023
Built responsive UI components using React.js.
Integrated REST API endpoints with JavaScript fetch API.

Full Stack Developer
Digital Labs, Pune | June 2023 - Present
Developing full-stack web applications using Node.js and MongoDB.

PROJECTS

E-Commerce Platform
Built an end-to-end e-commerce site with Node.js, React.js, and MongoDB.
Implemented JWT authentication and Redis caching.

CERTIFICATIONS
Full Stack Web Development - Udemy
JavaScript Algorithms and Data Structures - HackerRank
""".strip()


# Sample C — Missing certifications entirely, skills with mixed formatting,
#              experience section uses "Internships" header
RESUME_C = """
Ananya Iyer
ananya.iyer@devmail.in
+91-8899001122

Education

M.Tech in Data Science
SRM University | 2021-2023
CGPA 9.1

B.Sc in Computer Science
Anna University, Chennai | 2018-2021
CGPA: 8.2/10

Skills

Python  Flask  TensorFlow  Keras  Pandas  NumPy  scikit-learn  MySQL
Matplotlib  Jupyter  Git  AWS  Docker

Internships

Data Science Intern
Analytics Corp, Chennai | May 2022 - July 2022
Performed feature engineering and model training using scikit-learn.
Visualized results with Matplotlib and Seaborn.

Projects

Sentiment Analysis Engine
NLP project to classify movie reviews using TensorFlow and Keras.
Dataset preprocessing with Pandas and NumPy. Achieved 91% accuracy.

Fake News Detector
Trained a classifier using scikit-learn and Flask for serving predictions.
""".strip()


# Sample D — Garbled / minimal text (nearly empty, no structure)
RESUME_D = "  \n\n   \t  random text abc 123   \n\n  "


# ===========================================================================
# Helper: build a mock pdfplumber that "extracts" a given string
# ===========================================================================

def _mock_pdf_open(text: str):
    """
    Return a context-manager mock that makes pdfplumber.open() yield one page
    whose extract_text() returns *text*.
    """
    mock_page = MagicMock()
    mock_page.extract_text.return_value = text

    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]

    mock_ctx = MagicMock()
    mock_ctx.__enter__ = MagicMock(return_value=mock_pdf)
    mock_ctx.__exit__ = MagicMock(return_value=False)

    return mock_ctx


# ===========================================================================
# Test 1 — Correct email and phone extraction from a well-formatted resume
# ===========================================================================

class TestPersonalInfoExtraction:

    def test_email_extraction_sample_a(self):
        result = parse_resume(RESUME_A)
        assert result["personal_info"]["email"] == "priya.sharma@email.com"

    def test_phone_extraction_sample_a(self):
        result = parse_resume(RESUME_A)
        phone = result["personal_info"]["phone"]
        assert phone is not None
        # Must contain 10 digits (Indian number)
        digits = "".join(c for c in phone if c.isdigit())
        assert len(digits) >= 10

    def test_email_extraction_sample_b(self):
        result = parse_resume(RESUME_B)
        assert result["personal_info"]["email"] == "rahul.kumar@techmail.com"

    def test_phone_extraction_sample_b(self):
        result = parse_resume(RESUME_B)
        phone = result["personal_info"]["phone"]
        assert phone is not None
        digits = "".join(c for c in phone if c.isdigit())
        assert len(digits) >= 10

    def test_email_extraction_sample_c(self):
        result = parse_resume(RESUME_C)
        assert result["personal_info"]["email"] == "ananya.iyer@devmail.in"

    def test_phone_extraction_sample_c(self):
        result = parse_resume(RESUME_C)
        phone = result["personal_info"]["phone"]
        assert phone is not None
        digits = "".join(c for c in phone if c.isdigit())
        assert len(digits) >= 10


# ===========================================================================
# Test 2 — Correct skill extraction from all three samples
# ===========================================================================

class TestSkillExtraction:

    def test_comma_list_skills_sample_a(self):
        """Sample A has skills as a comma-separated list."""
        result = parse_resume(RESUME_A)
        skills = [s.lower() for s in result["skills"]]
        for expected in ["python", "django", "react", "postgresql", "docker", "aws", "git"]:
            assert expected in skills, f"Expected skill '{expected}' not found in {skills}"

    def test_ml_skills_sample_a(self):
        result = parse_resume(RESUME_A)
        skills = [s.lower() for s in result["skills"]]
        assert "machine learning" in skills
        assert "numpy" in skills or "pandas" in skills

    def test_bullet_skills_sample_b(self):
        """Sample B has skills as bullet points."""
        result = parse_resume(RESUME_B)
        skills = [s.lower() for s in result["skills"]]
        for expected in ["javascript", "node.js", "mongodb", "react.js", "docker", "linux"]:
            assert expected in skills, f"Expected skill '{expected}' not found in {skills}"

    def test_space_separated_skills_sample_c(self):
        """Sample C has skills as space-separated tokens."""
        result = parse_resume(RESUME_C)
        skills = [s.lower() for s in result["skills"]]
        for expected in ["python", "flask", "tensorflow", "keras", "pandas", "numpy"]:
            assert expected in skills, f"Expected skill '{expected}' not found in {skills}"

    def test_skills_are_unique(self):
        """No duplicate entries in skills list."""
        for resume in (RESUME_A, RESUME_B, RESUME_C):
            result = parse_resume(resume)
            skills = [s.lower() for s in result["skills"]]
            assert len(skills) == len(set(skills)), "Duplicate skills detected"

    def test_skills_no_fabrication(self):
        """Skills must come from the predefined keyword list, never invented."""
        from app.ai.resume_parser import _SKILL_KEYWORDS
        known = {s.lower() for s in _SKILL_KEYWORDS}
        result = parse_resume(RESUME_A)
        for skill in result["skills"]:
            assert skill.lower() in known, (
                f"Fabricated skill '{skill}' returned — not in predefined list"
            )


# ===========================================================================
# Test 3 — Missing section yields empty list, no crash, no fabrication
# ===========================================================================

class TestMissingSection:

    def test_no_certifications_returns_empty_list(self):
        """Sample C has no certifications section."""
        result = parse_resume(RESUME_C)
        assert isinstance(result["certifications"], list)
        assert result["certifications"] == [], (
            f"Expected empty certifications, got: {result['certifications']}"
        )

    def test_certifications_present_sample_a(self):
        """Sample A does have certifications — should not be empty."""
        result = parse_resume(RESUME_A)
        assert len(result["certifications"]) > 0

    def test_all_keys_always_present(self):
        """All top-level keys must be present even when some sections are absent."""
        required_keys = {"personal_info", "education", "skills", "experience",
                         "projects", "certifications"}
        for resume in (RESUME_A, RESUME_B, RESUME_C):
            result = parse_resume(resume)
            assert required_keys.issubset(result.keys()), (
                f"Missing keys: {required_keys - result.keys()}"
            )

    def test_personal_info_keys_always_present(self):
        for resume in (RESUME_A, RESUME_B, RESUME_C):
            result = parse_resume(resume)
            pi = result["personal_info"]
            assert "name" in pi
            assert "email" in pi
            assert "phone" in pi

    def test_no_placeholder_strings_in_missing_fields(self):
        """
        Fields that cannot be extracted must be None or [], never a
        placeholder like 'Not specified', 'N/A', 'Unknown', etc.
        """
        placeholders = {"not specified", "n/a", "unknown", "none", "na",
                        "not available", "tbd", "to be determined"}
        result = parse_resume(RESUME_C)

        def _check(value):
            if isinstance(value, str):
                assert value.lower() not in placeholders, (
                    f"Placeholder string found: '{value}'"
                )
            elif isinstance(value, list):
                for item in value:
                    _check(item)
            elif isinstance(value, dict):
                for v in value.values():
                    _check(v)

        _check(result)


# ===========================================================================
# Test 4 — Garbled / minimal text does not crash; returns mostly-None structure
# ===========================================================================

class TestGarbledInput:

    def test_garbled_input_does_not_raise(self):
        """parse_resume on minimal text must not raise any exception."""
        result = parse_resume(RESUME_D)
        assert isinstance(result, dict)

    def test_garbled_input_returns_expected_schema(self):
        result = parse_resume(RESUME_D)
        assert "personal_info" in result
        assert "skills" in result
        assert "education" in result
        assert "experience" in result
        assert "projects" in result
        assert "certifications" in result

    def test_garbled_input_personal_info_is_none(self):
        """No email or phone in garbled text."""
        result = parse_resume(RESUME_D)
        pi = result["personal_info"]
        assert pi["email"] is None
        assert pi["phone"] is None

    def test_garbled_input_lists_are_empty_or_sparse(self):
        """Garbled text should yield no skills, education, experience, etc."""
        result = parse_resume(RESUME_D)
        assert result["skills"] == []
        assert result["education"] == []
        assert result["experience"] == []
        assert result["certifications"] == []

    def test_empty_string_does_not_crash(self):
        result = parse_resume("")
        assert isinstance(result, dict)
        assert result["personal_info"]["email"] is None


# ===========================================================================
# Test 5 — extract_text_from_pdf raises ResumeExtractionError for
#            empty/whitespace-only "extracted" content (mocked at text level)
# ===========================================================================

class TestExtractTextFromPdf:

    def test_raises_on_empty_pdf_text(self):
        """
        When pdfplumber extracts nothing (e.g. scanned image PDF),
        ResumeExtractionError must be raised with a descriptive message.
        """
        with patch("pdfplumber.open", return_value=_mock_pdf_open("")):
            with pytest.raises(ResumeExtractionError) as exc_info:
                extract_text_from_pdf("fake_path.pdf")
        assert "scanned image" in str(exc_info.value).lower() or \
               "unable to extract" in str(exc_info.value).lower()

    def test_raises_on_whitespace_only_pdf_text(self):
        """A PDF that only yields whitespace/newlines should raise."""
        with patch("pdfplumber.open", return_value=_mock_pdf_open("   \n\n\t   \n")):
            with pytest.raises(ResumeExtractionError):
                extract_text_from_pdf("fake_path.pdf")

    def test_raises_on_near_empty_pdf_text(self):
        """Very short text (< 50 non-whitespace chars) should raise."""
        with patch("pdfplumber.open", return_value=_mock_pdf_open("Hi\n\n\n\n\n")):
            with pytest.raises(ResumeExtractionError):
                extract_text_from_pdf("fake_path.pdf")

    def test_returns_string_on_valid_text(self):
        """A PDF with real text should return a cleaned string, no exception."""
        valid_text = RESUME_A  # plenty of content
        with patch("pdfplumber.open", return_value=_mock_pdf_open(valid_text)):
            result = extract_text_from_pdf("fake_path.pdf")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_text_cleaning_collapses_excess_newlines(self):
        """Excessive blank lines in source should be collapsed to at most 2."""
        # Use enough text to exceed the _MIN_TEXT_LENGTH threshold (50 non-ws chars)
        filler = "A" * 60
        raw = f"Section Header One\n\n\n\n\n\nSection Header Two\n{filler}"
        with patch("pdfplumber.open", return_value=_mock_pdf_open(raw)):
            result = extract_text_from_pdf("fake_path.pdf")
        assert "\n\n\n" not in result

    def test_text_cleaning_strips_control_characters(self):
        """Non-printable control characters (except \\t\\n\\r) must be removed."""
        # \x00 - \x08 are control chars
        raw = "Priya\x00Sharma\x07\nSoftware\x01Engineer" + "x" * 60
        with patch("pdfplumber.open", return_value=_mock_pdf_open(raw)):
            result = extract_text_from_pdf("fake_path.pdf")
        assert "\x00" not in result
        assert "\x07" not in result
        assert "\x01" not in result


# ===========================================================================
# Test 6 — ResumeParsingError carries partial_data on failure
# ===========================================================================

class TestResumeParsingErrorPartialData:

    def test_partial_data_on_internal_error(self):
        """
        If something fails mid-parse, the exception's partial_data must
        contain whatever was extracted so far.
        """
        # Force an error after skills extraction by patching _extract_education
        with patch(
            "app.ai.resume_parser._extract_education",
            side_effect=RuntimeError("simulated failure"),
        ):
            with pytest.raises(ResumeParsingError) as exc_info:
                parse_resume(RESUME_A)

        exc = exc_info.value
        assert hasattr(exc, "partial_data")
        assert isinstance(exc.partial_data, dict)
        # Personal info and skills should have been populated before the error
        pd = exc.partial_data
        assert "personal_info" in pd
        assert "skills" in pd
        # The email should already be set
        assert pd["personal_info"]["email"] == "priya.sharma@email.com"

    def test_partial_data_has_all_keys(self):
        """partial_data must always carry all required keys."""
        with patch(
            "app.ai.resume_parser._extract_education",
            side_effect=RuntimeError("boom"),
        ):
            with pytest.raises(ResumeParsingError) as exc_info:
                parse_resume(RESUME_A)

        required = {"personal_info", "education", "skills", "experience",
                    "projects", "certifications"}
        assert required.issubset(exc_info.value.partial_data.keys())


# ===========================================================================
# Test 7 — Education section parsing sanity checks
# ===========================================================================

class TestEducationParsing:

    def test_education_list_not_empty_sample_a(self):
        result = parse_resume(RESUME_A)
        assert isinstance(result["education"], list)
        assert len(result["education"]) >= 1

    def test_education_has_degree_sample_a(self):
        result = parse_resume(RESUME_A)
        degrees = [e["degree"] for e in result["education"] if e["degree"]]
        assert any("tech" in d.lower() or "b." in d.lower() for d in degrees), (
            f"No B.Tech degree found in education: {result['education']}"
        )

    def test_education_cgpa_extracted_sample_a(self):
        result = parse_resume(RESUME_A)
        cgpas = [e["cgpa"] for e in result["education"] if e["cgpa"]]
        assert any("8.7" in c for c in cgpas), (
            f"CGPA 8.7 not found in education entries: {result['education']}"
        )

    def test_education_multiple_entries_sample_c(self):
        """Sample C has two education entries (M.Tech + B.Sc)."""
        result = parse_resume(RESUME_C)
        assert len(result["education"]) >= 2


# ===========================================================================
# Test 8 — Experience section parsing with variant section headers
# ===========================================================================

class TestExperienceParsing:

    def test_work_experience_header_detected_sample_b(self):
        """'WORK EXPERIENCE' header variant must still populate experience."""
        result = parse_resume(RESUME_B)
        assert isinstance(result["experience"], list)
        assert len(result["experience"]) >= 1

    def test_internships_header_detected_sample_c(self):
        """'Internships' header must still populate experience."""
        result = parse_resume(RESUME_C)
        assert isinstance(result["experience"], list)
        assert len(result["experience"]) >= 1

    def test_experience_duration_extracted_sample_a(self):
        result = parse_resume(RESUME_A)
        durations = [e["duration"] for e in result["experience"] if e["duration"]]
        assert len(durations) >= 1, f"No duration extracted: {result['experience']}"
