# CampusHire 🎓💼

> **Next-Generation Campus Placement & Recruitment Management System**

CampusHire is a comprehensive, production-grade web application designed to streamline and automate university campus recruitment. It connects **Students**, **Recruiters**, and **Placement Officers** into a single cohesive platform featuring automated eligibility evaluation, structured application lifecycle state machines, interview scheduling, real-time analytics dashboards, and report generation with CSV export.

---

## 📑 Table of Contents

- [Key Features](#-key-features)
- [System Architecture & Tech Stack](#-system-architecture--tech-stack)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Environment Variables](#-environment-variables)
- [Seeding Demo Data](#-seeding-demo-data)
- [Demo Credentials](#-demo-credentials)
- [Running the Application](#-running-the-application)
- [Interactive API Documentation](#-interactive-api-documentation)
- [Database Schema & Architecture](#-database-schema--architecture)
- [Testing Instructions](#-testing-instructions)
- [Phase 2 (Planned): AI Capabilities](#-phase-2-planned-ai-capabilities)

---

## ✨ Key Features

### 🎓 1. Student Portal
- **Profile & Resume Management**: Manage academic profile details (CGPA, graduating batch, backlogs, branch) and upload validated PDF resumes.
- **Job Discovery & Automated Eligibility Engine**: Browse active campus job openings with real-time criteria verification (minimum CGPA, eligible branches, backlog limits, graduating year).
- **Application Tracking**: View detailed timeline history for every submitted application across all lifecycle stages.
- **Interview Center**: Track upcoming and past interviews (Technical, HR, Managerial) with mode, date, and link details.
- **Real-Time Notifications**: Instant updates with unread count badge in navbar when an application status changes.

### 🏢 2. Recruiter Portal
- **Company Profile & Drive Postings**: Manage company profile and create/edit/publish job postings (`OPEN`, `CLOSED`, `DRAFT`).
- **Applicant Pipeline & Actions**: Filter and review candidates, view verified student resumes, and advance candidates (`SHORTLIST`, `SCHEDULE INTERVIEW`, `SELECT`, `REJECT`).
- **Interview Coordination**: Schedule single or multi-round interviews (Online / Offline) with meeting links, time slots, and record evaluation results (`PASSED`, `FAILED`, `NO_SHOW`).
- **Recruiter Notifications**: Receive alerts on new student applications and completed interview feedback.

### 📊 3. Placement Officer (Admin) Portal
- **Live Executive Dashboard**: Real-time KPI metrics computed directly from database queries (Total Students, Partner Companies, Active Drives, Total Applications, Placement Rate %).
- **Interactive Visualizations**: Charts powered by Recharts (Application Funnel, Recruitment Drive Status, Applications by Company, Department-wise Placement Rates).
- **Comprehensive Management Tables**: Paginated, searchable, and filterable tables for Students, Companies, Jobs, Applications, and Interviews.
- **Report Generation & CSV Export**: Generate custom reports filtered by Batch Year, Department, Company, and Job with one-click streaming CSV downloads.

### 🔒 4. Security & Audit Integrity
- **Role-Based Access Control (RBAC)**: JWT authentication with route guards for `STUDENT`, `RECRUITER`, and `PLACEMENT_OFFICER`.
- **Stateless Transition State Machine**: Enforces strict forward state transitions (`APPLIED` → `ELIGIBILITY_VERIFIED` → `SHORTLISTED` → `INTERVIEW_SCHEDULED` → `INTERVIEW` → `SELECTED`/`REJECTED`) and prevents duplicate applications.
- **Audit Logging**: Every status change is persisted in `application_status_history` with actor ID, timestamp, and transition remarks.

---

## 🛠️ System Architecture & Tech Stack

```
campushire/
├── backend/                  # FastAPI REST API Backend
│   ├── alembic/              # Database migration versions & configs
│   ├── app/
│   │   ├── ai/               # AI module placeholders (Phase 2)
│   │   ├── api/              # API routers (auth, admin, applications, jobs, students, etc.)
│   │   ├── core/             # Security, JWT tokens, configuration settings
│   │   ├── database/         # Database connection and base declarative model
│   │   ├── models/           # SQLAlchemy ORM mapped entities
│   │   ├── schemas/          # Pydantic v2 request/response models
│   │   └── services/         # Business logic (admin, application state machine, eligibility, reports)
│   ├── scripts/              # Seed scripts (seed_data.py)
│   └── tests/                # Pytest automated test suite (79+ tests)
└── frontend/                 # React 19 + Vite Frontend SPA
    ├── src/
    │   ├── api/              # Axios API clients (auth, student, recruiter, admin)
    │   ├── components/       # Reusable UI components (Navbar, Badges, Modals, Spinners)
    │   ├── layouts/          # Role layouts (StudentLayout, RecruiterLayout, PlacementOfficerLayout)
    │   ├── pages/            # View pages for Student, Recruiter, and Admin portals
    │   └── store/            # Zustand authentication store
```

### Technology Matrix

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Backend Framework** | **FastAPI** (Python 3.10+) | High-performance asynchronous API framework |
| **Database ORM** | **SQLAlchemy 2.0** | Type-safe declarative ORM with relationship mapping |
| **Database** | **MySQL / SQLite** | Relational storage with foreign key cascades |
| **Auth & Security** | **JWT + Passlib [Bcrypt]** | Secure password hashing and tokenized authorization |
| **Testing** | **Pytest + TestClient** | Automated unit and integration test suite |
| **Frontend SPA** | **React 19 + Vite** | High-velocity build tool and reactive UI framework |
| **Routing** | **React Router v7** | Role-protected client-side navigation |
| **State Management** | **Zustand** | Lightweight persisted authentication store |
| **Styling** | **Tailwind CSS** | Modern responsive styling with Dark/Light palette |
| **Charts** | **Recharts** | Interactive SVG analytics visualizations |

---

## 📋 Prerequisites

Before setting up CampusHire, ensure you have the following installed on your machine:
- **Python**: Version 3.10, 3.11, 3.12, or 3.13
- **Node.js**: Version 18.x, 20.x, or 22.x (with `npm`)
- **Git**
- **MySQL Server** (Optional: SQLite is supported out of the box for quick local evaluation)

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/campushire.git
cd campushire
```

---

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create a Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# On Linux / macOS:
source venv/bin/activate

# Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 3. Frontend Setup

```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install Node.js dependencies
npm install
```

---

## ⚙️ Environment Variables

### Backend (`backend/.env`)
Create a `.env` file in the `backend/` directory:

```ini
# Application Settings
PROJECT_NAME=CampusHire
API_V1_STR=/api/v1
SECRET_KEY=super-secret-key-change-this-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database Configuration (MySQL or SQLite)
# SQLite (Default local setup):
DATABASE_URL=sqlite:///./campushire.db
# MySQL Example:
# DATABASE_URL=mysql+pymysql://root:password@localhost:3306/campushire_db

# CORS Configuration
BACKEND_CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173","http://localhost:3000"]
```

### Frontend (`frontend/.env`)
Create a `.env` file in the `frontend/` directory:

```ini
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## 🌱 Seeding Demo Data

CampusHire includes a database seeder (`scripts/seed_data.py`) that clears and populates the database with realistic demo data:
- **4 Partner Companies** (TechCorp Solutions, DataInsight Analytics, CloudMasters Inc, CyberShield Security)
- **8 Diverse Student Profiles** with varied CGPAs (5.6 to 9.4), branches (CS, IT, ECE, Mech), backlog counts, and batches
- **6 Job Postings** across statuses (`OPEN`, `CLOSED`, `DRAFT`) with criteria boundaries
- **8 Candidate Applications** spanning all lifecycle stages (`APPLIED`, `SHORTLISTED`, `INTERVIEW_SCHEDULED`, `INTERVIEW`, `SELECTED`, `REJECTED`)
- **6 Interview Rounds** (Technical, HR, Assessment) with modes and feedback
- **6 In-App Notifications**

To execute the seed script:
```bash
cd backend
python scripts/seed_data.py
```

---

## 🔑 Demo Credentials

All seeded demo accounts share the password: `DemoPass@123`

| Role | Demo Email | Password | Profile Overview |
| :--- | :--- | :--- | :--- |
| **🎓 Student** | `student@campushire.demo` | `DemoPass@123` | **Alex River** (CS, 8.5 CGPA, 0 Backlogs, Active shortlist) |
| **🏢 Recruiter** | `recruiter@campushire.demo` | `DemoPass@123` | **Jane Smith** (Lead TA @ TechCorp Solutions) |
| **📊 Placement Officer** | `placement@campushire.demo` | `DemoPass@123` | **Dr. Arthur Vance** (Placement Head - Admin Dashboard) |

Additional student accounts: `priya.sharma@campushire.demo` (9.4 CGPA), `rahul.verma@campushire.demo` (7.8 CGPA), etc.

---

## 💻 Running the Application

### 1. Start the Backend Server
```bash
cd backend
# With virtual environment activated:
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
Backend will be available at: `http://127.0.0.1:8000`

### 2. Start the Frontend Dev Server
```bash
cd frontend
npm run dev
```
Frontend will be available at: `http://localhost:5173`

---

## 📖 Interactive API Documentation

FastAPI automatically generates interactive documentation for all endpoints:

- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI Schema**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 🏛️ Database Schema & Architecture

```
                 ┌───────────────┐
                 │     users     │
                 └───┬───────┬───┘
                     │       │
       ┌─────────────┘       └─────────────┐
       ▼                                   ▼
┌──────────────┐                   ┌──────────────┐
│   students   │                   │  recruiters  │
└───┬──────┬───┘                   └───┬──────┬───┘
    │      │                           │      │
    │      ▼                           │      ▼
    │  ┌─────────┐                     │  ┌───────────┐
    │  │ resumes │                     │  │ companies │
    │  └────┬────┘                     │  └─────┬─────┘
    ▼       │                          ▼        │
┌───────────┴──┐                   ┌────────────┴─┐
│ applications │◄──────────────────┤     jobs     │
└───┬──────┬───┘                   └──────────────┘
    │      │
    │      ▼
    │  ┌───────────────────────────┐
    │  │ application_status_history│
    │  └───────────────────────────┘
    ▼
┌────────────┐
│ interviews │
└────────────┘
```

### Core Entities
1. **User**: Authentication identity, role (`STUDENT`, `RECRUITER`, `PLACEMENT_OFFICER`), hashed password.
2. **Student**: Academic records (roll number, branch, year, CGPA, backlog count, skills JSON).
3. **Company**: Enterprise partner profile (name, industry, website, address, contact email).
4. **Recruiter**: Recruiter profile linked to a company and user identity.
5. **Job**: Postings with criteria (minimum CGPA, allowed branches, max backlogs, batch, salary package, status).
6. **Application**: Candidate submission linked to student, job, and resume with state-machine status.
7. **ApplicationStatusHistory**: Immutable audit record of every status transition.
8. **Interview**: Scheduled interview rounds (Technical, HR, Managerial, Assessment) with mode, link, and result.
9. **Notification**: User-specific notification events with unread tracking.

---

## 🧪 Testing Instructions

The backend features a comprehensive test suite (79+ tests) covering:
- Auth registration, duplicate email rejection, JWT issuance, profile retrieval
- Role-based authorization guards across all protected endpoints
- Eligibility engine rule validation (CGPA, branch, backlogs, batch year)
- Duplicate application prevention (`409 Conflict`)
- Application status transition state machine (forward progressions, terminal states, placement officer reopen)
- Interview scheduling & result updates
- Admin pagination on list endpoints (`page`, `page_size`, `total`, `total_pages`)
- Report generation (JSON aggregates and CSV file streaming export)

### Running Pytest Suite
```bash
cd backend
# Run all tests with verbose output:
pytest -v

# Run with test coverage:
pytest --cov=app tests/
```

### Running Frontend Production Build Validation
```bash
cd frontend
npm run build
```

---

## 🤖 AI Pipeline & Intelligence Engine

CampusHire features an integrated, production-ready AI layer designed for automated resume extraction, semantic talent matching, transparent weighted scoring, and intelligent candidate ranking.

```
┌──────────────────┐     ┌──────────────────────┐     ┌────────────────────────────┐
│   Resume PDF     │ ──► │  pdfplumber + spaCy  │ ──► │   Sentence-Transformers    │
│  (Uploaded File) │     │ (Section Extraction) │     │ (Dense Semantic Embedding) │
└──────────────────┘     └──────────────────────┘     └──────────────┬─────────────┘
                                                                     │
                                                                     ▼
┌──────────────────┐     ┌──────────────────────┐     ┌────────────────────────────┐
│ Ranked Candidate │ ◄── │   Weighted Scoring   │ ◄── │      Job Requirements      │
│   Leaderboard    │     │    Engine (4-Factor) │     │    (Skills, Exp, Edu, Desc)│
└──────────────────┘     └──────────────────────┘     └────────────────────────────┘
```

### 1. Architectural Components

1. **PDF Text & Section Extraction (`pdfplumber` + `spaCy`)**:
   - `pdfplumber` extracts high-fidelity raw text from candidate PDF resumes while cleaning weird control characters and formatting breaks.
   - `spaCy` (`en_core_web_sm`) processes text into structured entities: personal info (name, email, phone), technical skills taxonomy, categorized education degrees/institutions, and work experience/internship durations.
   - Resilient fallback: unparseable or scanned resumes trigger graceful `parsing_status = "failed"` without crashing upload or deleting stored files.

2. **Semantic Vector Embeddings (`Sentence-Transformers`)**:
   - Encodes job descriptions and resume text into 384-dimensional dense semantic vectors using `Sentence-Transformers`.
   - **Configurable Model**: Default model is `all-MiniLM-L6-v2` (fast, CPU-friendly), configurable via the `EMBEDDING_MODEL_NAME` environment variable.
   - **Intelligent Caching**: Embeddings are SHA-256 fingerprinted and cached on database rows (`Resume.embedding_hash`, `Job.embedding_hash`). Recomputed only when the underlying text is modified.
   - Normalized cosine similarity scaled to `0.0 – 100.0%`.

3. **Multi-Factor Weighted Scoring Engine**:
   - Computes an overall composite AI match score (`0.0 – 100.0%`) based on four central, configurable weights (`app/ai/scoring_config.py`):
     - **Semantic Relevance (`SEMANTIC_WEIGHT = 0.50`)**: Overall conceptual alignment between candidate background and job profile.
     - **Skill Alignment (`SKILL_WEIGHT = 0.25`)**: Keyword overlap with mandatory required skills weighted double (`2.0x`) compared to preferred skills (`1.0x`).
     - **Experience Relevance (`EXPERIENCE_WEIGHT = 0.15`)**: Quantitative experience duration compared against job requirements.
     - **Education Alignment (`EDUCATION_WEIGHT = 0.10`)**: Degree qualification and branch relevance.
   - *Constraint*: The four weights sum strictly to `1.0`.

4. **Applicant Ranking & Recruiter Leaderboard**:
   - Eligible applicants are sorted descending by composite `ai_score`.
   - Deterministic tie-breaking by earlier `applied_at` timestamp.
   - Auto-scored on page load with manual on-demand recalculation available.

5. **AI Job Recommendations for Students**:
   - Compares student's active resume embedding against all active campus job openings (`GET /students/recommended-jobs`).
   - Returns top recommendations with **independent eligibility evaluation** — a job can be highly recommended for skills while remaining marked ineligible due to hard constraints (e.g. CGPA, branch, or backlogs).

> [!NOTE]
> **Assistive AI Principle**: AI scores in CampusHire are strictly assistive screening aids to help recruiters prioritize evaluation — they never represent automated hiring or rejection decisions. Final selection is always human-driven.

---

## 📡 API Endpoints Reference

### 🤖 AI & Matching Endpoints
- `POST /resumes/{id}/parse` — Trigger structured AI parsing of a stored PDF resume.
- `GET /applications/{id}/match-analysis` — Get transparent multi-factor AI scoring breakdown and skill comparison.
- `POST /jobs/{job_id}/recalculate-scores` — Recalculate applicant scores and rankings on demand.
- `GET /jobs/{job_id}/applications/export?top_k={n}&format=csv` — Export top-N or all ranked applicants as CSV with complete AI metrics.
- `GET /students/recommended-jobs` — Retrieve top job recommendations for logged-in student based on resume semantic similarity.

### 🎓 Student Endpoints
- `GET /students/me` — Retrieve student profile and completion percentage.
- `PUT /students/me` — Update student profile, skills, education, and experience.
- `POST /students/resume` — Upload PDF resume with inline automated AI parsing.
- `GET /students/resume` — Get active primary resume metadata.
- `GET /students/me/parsed-resume` — Retrieve parsed structured data for profile prefilling.
- `GET /students/jobs` — Browse open campus recruitment drives with real-time eligibility status.
- `POST /applications/{job_id}/apply` — Apply for a job posting.
- `GET /applications` — List submitted applications with lifecycle status and ranks.
- `GET /applications/{id}` — Application detail with complete status history audit timeline.

### 🏢 Recruiter Endpoints
- `POST /jobs` — Create and publish recruitment drives (`DRAFT`, `OPEN`, `CLOSED`).
- `GET /jobs` — List company jobs with application metrics.
- `GET /jobs/{job_id}/applications` — View ranked applicants list with AI scores and filters.
- `PATCH /applications/{id}/status` — Advance applicant through the lifecycle state machine.
- `POST /interviews` — Schedule technical/HR interview rounds.
- `PATCH /interviews/{id}` — Submit interview evaluation results (`PASSED`, `FAILED`, `NO_SHOW`).

### 📊 Placement Officer Endpoints
- `GET /admin/dashboard` — Live placement metrics, KPI counters, and placement rates.
- `GET /admin/students` — Paginated and searchable student registry.
- `GET /admin/jobs` — Comprehensive placement drives oversight.
- `GET /admin/reports` — Aggregated recruitment reports with custom department/batch filters.
- `GET /admin/reports/export` — Stream generated placement report as CSV.

---

## 🧪 Testing Instructions

CampusHire includes a comprehensive test suite with **184+ passing automated tests** across unit, service, API, and full end-to-end integration levels:
- Full E2E AI pipeline (parse → embed → score → rank → export)
- Resilient failure recovery (corrupted resumes do not crash requests or block other applicants)
- Caching verification (embeddings reuse verified via SHA-256 hashes)
- Role-based authorization & route guards
- State-machine lifecycle validation and immutable audit logs
- Multi-factor scoring configuration assertion

### Running the Pytest Suite
```bash
cd backend
# Run all tests with verbose output:
pytest -v

# Run with test coverage report:
pytest --cov=app tests/
```

### Running Frontend Validation
```bash
cd frontend
npm run build
```

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
