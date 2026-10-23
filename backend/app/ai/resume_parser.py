"""
app/ai/resume_parser.py
=======================
Isolated resume parsing utilities for CampusHire.

Provides:
  - extract_text_from_pdf(file_path) -> str
  - parse_resume(text) -> dict

Custom exceptions:
  - ResumeExtractionError  (raised when PDF yields no usable text)
  - ResumeParsingError     (raised when parse_resume fails unexpectedly;
                             carries .partial_data for whatever was extracted)

No FastAPI routes or SQLAlchemy models are imported here.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

import pdfplumber

# ---------------------------------------------------------------------------
# spaCy — loaded once at module import time for performance.
# ---------------------------------------------------------------------------
import spacy

try:
    _NLP = spacy.load("en_core_web_sm")
except OSError:
    # Allow import to succeed even if the model hasn't been downloaded yet;
    # parse_resume will raise a clear error when _NLP is None.
    _NLP = None  # type: ignore[assignment]


# ===========================================================================
# Custom exceptions
# ===========================================================================


class ResumeExtractionError(Exception):
    """Raised when pdfplumber cannot extract usable text from a PDF."""


class ResumeParsingError(Exception):
    """
    Raised when parse_resume encounters an unexpected, unrecoverable error.

    Attributes
    ----------
    partial_data : dict
        Whatever structured data was successfully extracted before the failure.
        Calling code may inspect this and decide whether to persist it.
    """

    def __init__(self, message: str, partial_data: dict | None = None) -> None:
        super().__init__(message)
        self.partial_data: dict = partial_data or {}


# ===========================================================================
# Skill keyword list  (>=80 common tech skills, grouped for readability)
# ===========================================================================

_SKILL_KEYWORDS: list[str] = [
    # --- Programming Languages ---
    "Python", "Java", "JavaScript", "TypeScript", "C", "C++", "C#", "Go",
    "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Scala", "R", "MATLAB",
    "Perl", "Shell", "Bash", "PowerShell", "Dart", "Lua", "Haskell",
    # --- Web / Frontend ---
    "HTML", "CSS", "React", "React.js", "Next.js", "Vue", "Vue.js",
    "Angular", "Svelte", "jQuery", "Bootstrap", "Tailwind",
    # --- Backend / Frameworks ---
    "Node.js", "Express", "FastAPI", "Django", "Flask", "Spring Boot",
    "Laravel", "Rails", "ASP.NET", "NestJS",
    # --- Databases ---
    "MySQL", "PostgreSQL", "SQLite", "MongoDB", "Redis", "Cassandra",
    "DynamoDB", "Elasticsearch", "MariaDB", "Oracle", "SQL Server",
    "Firebase", "Supabase",
    # --- Cloud / DevOps / Tools ---
    "AWS", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes",
    "Terraform", "Ansible", "Jenkins", "GitHub Actions", "CI/CD",
    "Linux", "Git", "GitHub", "GitLab", "Nginx", "Apache",
    # --- AI / ML / Data Science ---
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision",
    "TensorFlow", "PyTorch", "Keras", "scikit-learn", "Pandas",
    "NumPy", "Matplotlib", "Seaborn", "OpenCV", "Hugging Face",
    "LangChain", "Reinforcement Learning", "Data Science",
    "Feature Engineering", "Model Deployment", "MLOps",
    # --- Mobile ---
    "Android", "iOS", "Flutter", "React Native",
    # --- Misc / Tools ---
    "REST API", "GraphQL", "WebSockets", "gRPC", "Microservices",
    "Agile", "Scrum", "Jira", "Figma", "Postman", "Jupyter",
    "Hadoop", "Spark", "Kafka", "RabbitMQ",
]

# Build a lower-cased set for fast membership tests
_SKILL_LOWER: dict[str, str] = {s.lower(): s for s in _SKILL_KEYWORDS}


# ===========================================================================
# Section-heading detection helpers
# ===========================================================================

# Map of canonical section names to list of regex patterns that match them
_SECTION_PATTERNS: dict[str, list[str]] = {
    "education": [
        r"education",
        r"academic\s+background",
        r"academic\s+qualifications?",
        r"qualifications?",
        r"academic\s+details",
    ],
    "skills": [
        r"skills?",
        r"technical\s+skills?",
        r"core\s+competenc(?:ies|y)",
        r"technologies",
        r"tech\s+stack",
        r"expertise",
        r"key\s+skills?",
    ],
    "experience": [
        r"(?:work\s+)?experience",
        r"employment\s+(?:history|record)",
        r"professional\s+(?:experience|background|summary)",
        r"internship(?:s)?",
        r"work\s+history",
    ],
    "projects": [
        r"projects?",
        r"personal\s+projects?",
        r"academic\s+projects?",
        r"key\s+projects?",
        r"portfolio",
    ],
    "certifications": [
        r"certifications?",
        r"certificates?",
        r"credentials?",
        r"courses?\s+&?\s*certifications?",
        r"professional\s+development",
        r"licenses?\s+(?:&\s+)?certifications?",
    ],
}

# Compile a single regex per section for efficient matching
_SECTION_RE: dict[str, re.Pattern[str]] = {
    section: re.compile(
        r"^(?:" + "|".join(pats) + r")\s*:?\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    for section, pats in _SECTION_PATTERNS.items()
}


def _is_section_header(line: str) -> str | None:
    """
    Return the canonical section name if *line* looks like a section header,
    else return None.
    """
    stripped = line.strip()
    if not stripped:
        return None
    for section, pat in _SECTION_RE.items():
        if pat.match(stripped):
            return section
    return None


def _split_into_sections(text: str) -> dict[str, str]:
    """
    Segment *text* into a dict keyed by canonical section name.
    Lines that appear before any known header go into "header" (used for
    personal info / name detection).
    """
    sections: dict[str, list[str]] = {"header": []}
    current_section = "header"

    for line in text.splitlines():
        detected = _is_section_header(line)
        if detected is not None:
            current_section = detected
            if current_section not in sections:
                sections[current_section] = []
        else:
            sections.setdefault(current_section, []).append(line)

    return {k: "\n".join(v) for k, v in sections.items()}


# ===========================================================================
# PDF text extraction
# ===========================================================================

# Minimum number of non-whitespace characters required to count as "real" text
_MIN_TEXT_LENGTH = 50


def extract_text_from_pdf(file_path: str) -> str:
    """
    Extract and clean text from a PDF file using pdfplumber.

    Parameters
    ----------
    file_path : str
        Absolute or relative path to the PDF file.

    Returns
    -------
    str
        Cleaned, readable text with section-level line breaks preserved.

    Raises
    ------
    ResumeExtractionError
        If the PDF yields fewer than ``_MIN_TEXT_LENGTH`` non-whitespace
        characters (typical of scanned-image PDFs or corrupted files).
    """
    raw_pages: list[str] = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            raw_pages.append(page_text)

    raw = "\n\n".join(raw_pages)

    # Step 1: Remove control characters except normal whitespace (\t\n\r)
    cleaned_chars = []
    for ch in raw:
        cat = unicodedata.category(ch)
        if ch in ("\t", "\n", "\r") or cat[0] != "C":
            cleaned_chars.append(ch)
    text = "".join(cleaned_chars)

    # Step 2: Normalise Unicode to NFC
    text = unicodedata.normalize("NFC", text)

    # Step 3: Replace tabs with spaces
    text = text.replace("\t", " ")

    # Step 4: Collapse runs of spaces (but not newlines)
    text = re.sub(r"[ ]{2,}", " ", text)

    # Step 5: Collapse more than 2 consecutive newlines into exactly 2
    #         (preserve paragraph / section breaks, but kill excessive gaps)
    text = re.sub(r"\n{3,}", "\n\n", text)

    # Step 6: Strip leading/trailing whitespace per line while keeping blanks
    lines = [ln.rstrip() for ln in text.splitlines()]
    text = "\n".join(lines).strip()

    # Validate
    if len(text.replace(" ", "").replace("\n", "")) < _MIN_TEXT_LENGTH:
        raise ResumeExtractionError(
            "Unable to extract text from this resume. "
            "It may be a scanned image or corrupted file."
        )

    return text


# ===========================================================================
# Regex helpers
# ===========================================================================

_EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

_PHONE_RE = re.compile(
    r"""
    (?:
        # +country-code variants
        (?:\+\d{1,3}[\s\-.]?)          # +91 / +1 / +44
        (?:\(?\d{1,4}\)?[\s\-.]?)?     # optional area code in parens
        \d{3,5}[\s\-.]?\d{3,5}         # subscriber number
    |
        # plain 10-digit (Indian / US style, optional separators)
        \(?\d{3,5}\)?[\s\-.]?\d{3,5}[\s\-.]?\d{4,5}
    )
    """,
    re.VERBOSE,
)

_YEAR_RE = re.compile(r"\b(20\d{2})\b")

_CGPA_RE = re.compile(
    r"""
    (?:cgpa|gpa|grade|score|percentage|%)\s*[:\-]?\s*
    (\d+\.\d{1,2})
    |
    (\d+\.\d{1,2})\s*/\s*(?:4\.0|5\.0|10\.0|10)
    |
    \b(\d\.\d{1,2})\b
    """,
    re.IGNORECASE | re.VERBOSE,
)

_DURATION_RE = re.compile(
    r"""
    (?:
        # Month Year - Month Year
        (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|
           Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|
           Dec(?:ember)?)
        \s+\d{4}
        \s*[-]+\s*
        (?:
            (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|
               Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|
               Dec(?:ember)?)
            \s+\d{4}
            | Present | Current | Till\s+date | Ongoing
        )
    |
        # Year - Year  or  Year - Present
        \d{4}\s*[-]+\s*(?:\d{4}|Present|Current|Ongoing)
    |
        # (Month) YYYY to (Month) YYYY
        (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|
           Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|
           Dec(?:ember)?)
        \s+\d{4}\s+to\s+
        (?:
            (?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|
               Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|
               Dec(?:ember)?)
            \s+\d{4}
            | Present
        )
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)

# Degrees
_DEGREE_KEYWORDS = [
    r"B\.?Tech",
    r"B\.?E\.?",
    r"B\.?Sc",
    r"B\.?Com",
    r"B\.?A",
    r"M\.?Tech",
    r"M\.?E\.?",
    r"M\.?Sc",
    r"MBA",
    r"MCA",
    r"BCA",
    r"Ph\.?D",
    r"Bachelor(?:'s)?(?:\s+of\s+\w+)*",
    r"Master(?:'s)?(?:\s+of\s+\w+)*",
    r"Diploma",
    r"Associate(?:'s)?",
    r"Doctor(?:ate)?(?:\s+of\s+\w+)*",
]
_DEGREE_RE = re.compile(
    r"\b(" + "|".join(_DEGREE_KEYWORDS) + r")\b",
    re.IGNORECASE,
)

# Departments / disciplines
_DEPT_KEYWORDS = [
    "Computer Science", "Information Technology", "Electronics",
    "Electrical Engineering", "Mechanical Engineering", "Civil Engineering",
    "Chemical Engineering", "Data Science", "Artificial Intelligence",
    "Software Engineering", "Biotechnology", "Aerospace", "Instrumentation",
]
_DEPT_RE = re.compile(
    r"\b(" + "|".join(re.escape(d) for d in _DEPT_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


# ===========================================================================
# Extraction helpers for each section
# ===========================================================================


def _extract_email(text: str) -> str | None:
    m = _EMAIL_RE.search(text)
    return m.group(0) if m else None


def _extract_phone(text: str) -> str | None:
    m = _PHONE_RE.search(text)
    if not m:
        return None
    raw = m.group(0).strip()
    # Sanity: must contain at least 7 digits
    if len(re.sub(r"\D", "", raw)) < 7:
        return None
    return raw


def _extract_name_spacy(header_text: str) -> str | None:
    """
    Use spaCy NER to find a PERSON entity near the top of the resume.
    Only trusts the first PERSON entity found within the first 400 characters.
    Returns None if spaCy is not loaded or no confident match is found.
    """
    if _NLP is None:
        return None
    snippet = header_text[:400]
    doc = _NLP(snippet)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip()
            # Reject very short or all-uppercase strings (often section labels)
            if len(name) >= 4 and not name.isupper():
                return name
    return None


def _extract_skills(text: str) -> list[str]:
    """
    Case-insensitive match of skill keywords against the full resume text.
    Returns unique matched canonical skill names in their original casing.
    """
    found: list[str] = []
    text_lower = text.lower()
    seen: set[str] = set()

    for lower_kw, canonical in _SKILL_LOWER.items():
        # Word-boundary aware search (handles multi-word skills too)
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(lower_kw) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, text_lower):
            if canonical not in seen:
                found.append(canonical)
                seen.add(canonical)

    return found


def _extract_education(section_text: str) -> list[dict[str, str | None]]:
    """
    Parse education section into a list of entries.
    Heuristic: each non-empty block (separated by blank lines) is one entry.
    """
    entries: list[dict[str, str | None]] = []
    blocks = _split_blocks(section_text)

    for block in blocks:
        if not block.strip():
            continue
        entry: dict[str, str | None] = {
            "degree": None,
            "institution": None,
            "department": None,
            "graduation_year": None,
            "cgpa": None,
        }

        # Degree
        dm = _DEGREE_RE.search(block)
        if dm:
            entry["degree"] = dm.group(0).strip()

        # Department
        dept_m = _DEPT_RE.search(block)
        if dept_m:
            entry["department"] = dept_m.group(0).strip()

        # Graduation year (most recent 4-digit year in block)
        years = _YEAR_RE.findall(block)
        if years:
            entry["graduation_year"] = max(years)

        # CGPA
        cgpa_m = _CGPA_RE.search(block)
        if cgpa_m:
            val = cgpa_m.group(1) or cgpa_m.group(2) or cgpa_m.group(3)
            if val:
                entry["cgpa"] = val

        # Institution
        inst_re = re.compile(
            r"\b([\w\s,\.]+(?:University|College|Institute|School|IIT|NIT|BITS|VIT"
            r"|Anna University|Amrita|SRM|Manipal|JNTU|LPU)[\w\s,\.]*)\b",
            re.IGNORECASE,
        )
        inst_m = inst_re.search(block)
        if inst_m:
            entry["institution"] = inst_m.group(0).strip()

        # Only add entry if at least one field was found
        if any(v is not None for v in entry.values()):
            entries.append(entry)

    return entries


def _extract_experience(section_text: str) -> list[dict[str, str | None]]:
    """
    Parse experience/work history into a list of entries.
    """
    entries: list[dict[str, str | None]] = []
    blocks = _split_blocks(section_text)

    for block in blocks:
        if not block.strip():
            continue
        entry: dict[str, str | None] = {
            "company": None,
            "role": None,
            "duration": None,
            "description": None,
        }

        # Duration
        dur_m = _DURATION_RE.search(block)
        if dur_m:
            entry["duration"] = dur_m.group(0).strip()

        # Role
        role_re = re.compile(
            r"\b((?:[\w\s]+\s+)?(?:Engineer|Developer|Analyst|Intern(?:ship)?|"
            r"Manager|Architect|Designer|Scientist|Researcher|Lead|Consultant|"
            r"Specialist|Associate|Coordinator|Executive|Officer)(?:\s+[\w\s]+)?)\b",
            re.IGNORECASE,
        )
        role_m = role_re.search(block)
        if role_m:
            entry["role"] = role_m.group(0).strip()

        # Company
        company_re = re.compile(
            r"\b([\w\s&,\.]+(?:Ltd\.?|Inc\.?|Pvt\.?|Corp\.?|Technologies|"
            r"Solutions|Systems|Services|Labs?|Studio|Software|Digital|"
            r"Group|Company|Co\.)[\w\s,\.]*)\b",
            re.IGNORECASE,
        )
        comp_m = company_re.search(block)
        if comp_m:
            entry["company"] = comp_m.group(0).strip()

        # Description: everything else
        desc_lines = [
            ln.strip()
            for ln in block.splitlines()
            if ln.strip()
            and not (dur_m and dur_m.group(0) in ln)
            and not (role_m and role_m.group(0) in ln)
            and not (comp_m and comp_m.group(0) in ln)
        ]
        if desc_lines:
            entry["description"] = " ".join(desc_lines)

        if any(v is not None for v in entry.values()):
            entries.append(entry)

    return entries


def _extract_projects(section_text: str) -> list[dict[str, Any]]:
    """
    Parse projects section into a list of entries.
    """
    entries: list[dict[str, Any]] = []
    blocks = _split_blocks(section_text)

    for block in blocks:
        if not block.strip():
            continue
        entry: dict[str, Any] = {
            "title": None,
            "technologies": [],
            "description": None,
        }

        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue

        # Title: typically the first non-empty line (often bold / short)
        first_line = lines[0]
        if len(first_line) <= 120:
            entry["title"] = first_line

        # Technologies: intersect the block text with skill list
        entry["technologies"] = _extract_skills(block)

        # Description: remaining lines after the title
        if len(lines) > 1:
            entry["description"] = " ".join(lines[1:])

        if entry["title"] or entry["technologies"] or entry["description"]:
            entries.append(entry)

    return entries


def _extract_certifications(section_text: str) -> list[dict[str, str | None]]:
    """
    Parse certifications section into a list of entries.
    """
    entries: list[dict[str, str | None]] = []

    lines = [ln.strip() for ln in section_text.splitlines() if ln.strip()]

    # Known issuers
    issuer_re = re.compile(
        r"\b((?:by\s+)?[\w\s&,\.]+(?:Coursera|Udemy|edX|LinkedIn|Google|Microsoft|"
        r"Amazon|AWS|Oracle|IBM|Cisco|CompTIA|PMI|NASSCOM|Infosys|TCS|"
        r"HackerRank|HackerEarth|Udacity|NPTEL)[\w\s,\.]*)",
        re.IGNORECASE,
    )

    for line in lines:
        if not line:
            continue
        entry: dict[str, str | None] = {"name": None, "issuer": None}

        iss_m = issuer_re.search(line)
        if iss_m:
            entry["issuer"] = iss_m.group(0).strip().lstrip("by").strip()
            name_part = line[: iss_m.start()].strip().rstrip("-|,:").strip()
            if name_part:
                entry["name"] = name_part
            else:
                entry["name"] = line.strip()
        else:
            entry["name"] = line

        if entry["name"] or entry["issuer"]:
            entries.append(entry)

    return entries


def _split_blocks(text: str) -> list[str]:
    """
    Split a section's text into logical 'entry' blocks separated by blank lines.
    """
    blocks = re.split(r"\n{2,}", text.strip())
    return [b for b in blocks if b.strip()]


# ===========================================================================
# Main public API
# ===========================================================================


def parse_resume(text: str) -> dict:
    """
    Parse the plain text of a resume into structured data.

    Parameters
    ----------
    text : str
        Plain text extracted from a resume (e.g. via extract_text_from_pdf).

    Returns
    -------
    dict with keys:
        personal_info, education, skills, experience, projects, certifications

    Raises
    ------
    ResumeParsingError
        If an unexpected error occurs.  The exception's ``.partial_data``
        attribute contains whatever was successfully extracted before the error.

    Notes
    -----
    Fields that cannot be confidently extracted are left as None or [].
    No placeholder strings are ever inserted.
    """
    if _NLP is None:
        raise ResumeParsingError(
            "spaCy model 'en_core_web_sm' is not available. "
            "Run: python -m spacy download en_core_web_sm"
        )

    # Accumulate partial results so they can be returned on error
    partial: dict = {
        "personal_info": {"name": None, "email": None, "phone": None},
        "education": [],
        "skills": [],
        "experience": [],
        "projects": [],
        "certifications": [],
    }

    try:
        # 1. Segment resume into sections
        sections = _split_into_sections(text)
        header_text = sections.get("header", "")

        # 2. Personal info
        partial["personal_info"]["email"] = _extract_email(text)
        partial["personal_info"]["phone"] = _extract_phone(text)
        partial["personal_info"]["name"] = _extract_name_spacy(header_text or text[:400])

        # 3. Skills
        partial["skills"] = _extract_skills(text)

        # 4. Education
        partial["education"] = _extract_education(sections.get("education", ""))

        # 5. Experience
        partial["experience"] = _extract_experience(sections.get("experience", ""))

        # 6. Projects
        partial["projects"] = _extract_projects(sections.get("projects", ""))

        # 7. Certifications
        partial["certifications"] = _extract_certifications(
            sections.get("certifications", "")
        )

        return partial

    except ResumeParsingError:
        raise
    except Exception as exc:
        raise ResumeParsingError(
            f"Unexpected error while parsing resume: {exc}",
            partial_data=partial,
        ) from exc
