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

## 🔮 Phase 2 (Planned): AI Capabilities

The following AI-powered capabilities are intentionally designed into the architecture and scheduled for Phase 2 implementation in `backend/app/ai`:

1. **AI Resume Parsing & Extraction**:
   - Deep extraction of structured work experience, education, and certified skills directly from uploaded PDF resumes into normalized taxonomy entities.
2. **Semantic Job-to-Resume Matching**:
   - Vector embedding similarity scoring (e.g. via Gemini embeddings / sentence-transformers) comparing job requirements with student resumes beyond simple keyword matching.
3. **Automated Applicant Ranking & Scoring**:
   - Weighted multi-factor candidate scoring (Skill match + Academic baseline + Project relevance) generating candidate fit percentiles.
4. **AI Interview Assistant**:
   - Automated question generation based on candidate resume strengths and job description requirements.

*Currently, all AI score and rank indicators in UI dashboards intentionally display "Pending AI analysis" as a placeholder for Phase 2.*

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.
