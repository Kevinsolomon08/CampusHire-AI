#!/usr/bin/env python
"""
CampusHire Seed Data Script
Populates the database with realistic demo data for testing and demonstration.

Demo Credentials (use any of these to log in):
  - Student:           student@campushire.demo / DemoPass@123
  - Recruiter:         recruiter@campushire.demo / DemoPass@123
  - Placement Officer: placement@campushire.demo / DemoPass@123

All demo accounts share the same password for simplicity during demos.

Run from backend root:
    python scripts/seed_data.py
"""

from __future__ import annotations

import sys
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Set stdout/stderr encoding to utf-8 if possible or replace unsupported characters
if hasattr(sys.stdout, "buffer") and sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if hasattr(sys.stderr, "buffer") and sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add backend root to path so we can import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.core.security import hash_password
from app.database.connection import SessionLocal, engine
from app.models.models import (
    Application,
    ApplicationStatus,
    ApplicationStatusHistory,
    Company,
    Interview,
    InterviewMode,
    InterviewResult,
    InterviewRound,
    Job,
    JobStatus,
    Notification,
    Recruiter,
    Resume,
    Student,
    User,
    UserRole,
)

# Demo password (hashed for all demo users)
DEMO_PASSWORD = "DemoPass@123"
DEMO_PASSWORD_HASHED = hash_password(DEMO_PASSWORD)

# Demo credentials to print at end
DEMO_CREDENTIALS = {
    "student": {
        "email": "student@campushire.demo",
        "password": DEMO_PASSWORD,
        "name": "Alex River",
        "role": "STUDENT (CS, CGPA 8.5, 0 Backlogs)",
    },
    "recruiter": {
        "email": "recruiter@campushire.demo",
        "password": DEMO_PASSWORD,
        "name": "Jane Smith",
        "role": "RECRUITER (TechCorp Solutions)",
    },
    "placement_officer": {
        "email": "placement@campushire.demo",
        "password": DEMO_PASSWORD,
        "name": "Dr. Arthur Vance",
        "role": "PLACEMENT_OFFICER (Head of Placements)",
    },
}


def seed_database():
    """Seed the database with realistic demo data."""
    db = SessionLocal()

    try:
        # Clear existing data in reverse dependency order
        print("[*] Clearing existing data...")
        db.query(Notification).delete()
        db.query(Interview).delete()
        db.query(ApplicationStatusHistory).delete()
        db.query(Application).delete()
        db.query(Resume).delete()
        db.query(Job).delete()
        db.query(Recruiter).delete()
        db.query(Student).delete()
        db.query(User).delete()
        db.query(Company).delete()
        db.commit()

        # =====================================================================
        # 1. Create Demo Users (Student, Recruiter, Placement Officer)
        # =====================================================================
        print("\n[*] Creating primary demo users...")

        student_user = User(
            email="student@campushire.demo",
            hashed_password=DEMO_PASSWORD_HASHED,
            role=UserRole.STUDENT,
            full_name="Alex River",
            is_active=True,
        )
        db.add(student_user)
        db.flush()

        recruiter_user = User(
            email="recruiter@campushire.demo",
            hashed_password=DEMO_PASSWORD_HASHED,
            role=UserRole.RECRUITER,
            full_name="Jane Smith",
            is_active=True,
        )
        db.add(recruiter_user)
        db.flush()

        recruiter_user_2 = User(
            email="recruiter.datainsight@campushire.demo",
            hashed_password=DEMO_PASSWORD_HASHED,
            role=UserRole.RECRUITER,
            full_name="Marcus Brody",
            is_active=True,
        )
        db.add(recruiter_user_2)
        db.flush()

        placement_officer_user = User(
            email="placement@campushire.demo",
            hashed_password=DEMO_PASSWORD_HASHED,
            role=UserRole.PLACEMENT_OFFICER,
            full_name="Dr. Arthur Vance",
            is_active=True,
        )
        db.add(placement_officer_user)
        db.flush()

        print("  + Created demo accounts (Alex River, Jane Smith, Dr. Arthur Vance)")

        # =====================================================================
        # 2. Create Companies
        # =====================================================================
        print("\n[*] Creating partner companies...")

        companies = [
            Company(
                name="TechCorp Solutions",
                website="https://techcorp.example.com",
                industry="Software & Cloud Services",
                description="Global enterprise software innovator building next-generation SaaS architectures.",
                contact_email="careers@techcorp.example.com",
                contact_phone="+1-800-TECH-CORP",
                address="San Francisco, CA",
            ),
            Company(
                name="DataInsight Analytics",
                website="https://datainsight.example.com",
                industry="Data Science & Analytics",
                description="Transforming big enterprise data into high-velocity machine learning decisions.",
                contact_email="hr@datainsight.example.com",
                contact_phone="+1-800-DATA-ANA",
                address="New York, NY",
            ),
            Company(
                name="CloudMasters Inc",
                website="https://cloudmasters.example.com",
                industry="Cloud Infrastructure & DevOps",
                description="Multi-cloud orchestration and reliable scalable cloud hosting architectures.",
                contact_email="recruitment@cloudmasters.example.com",
                contact_phone="+1-800-CLOUD-M",
                address="Seattle, WA",
            ),
            Company(
                name="CyberShield Security",
                website="https://cybershield.example.com",
                industry="Cybersecurity & Defense",
                description="Zero-trust security suites and automated enterprise vulnerability scanning.",
                contact_email="talent@cybershield.example.com",
                contact_phone="+1-800-CYBER-SEC",
                address="Austin, TX",
            ),
        ]
        for company in companies:
            db.add(company)
        db.flush()
        print(f"  + Created {len(companies)} companies")

        # =====================================================================
        # 3. Create Recruiter Profiles
        # =====================================================================
        print("\n[*] Creating recruiter profiles...")

        recruiter_1 = Recruiter(
            user_id=recruiter_user.id,
            company_id=companies[0].id,  # TechCorp Solutions
            designation="Senior Talent Acquisition Lead",
            phone="+1-800-555-0199",
        )
        db.add(recruiter_1)

        recruiter_2 = Recruiter(
            user_id=recruiter_user_2.id,
            company_id=companies[1].id,  # DataInsight Analytics
            designation="University Relations Manager",
            phone="+1-800-555-0288",
        )
        db.add(recruiter_2)
        db.flush()
        print("  + Created recruiter profiles linked to TechCorp & DataInsight")

        # =====================================================================
        # 4. Create Students (Varied CGPA, Branches, Backlogs, Batches)
        # =====================================================================
        print("\n[*] Creating student profiles with diverse academic profiles...")

        student_configs = [
            # 1. Demo Student: CS, high CGPA, 0 backlogs -> Eligible for most
            {
                "user_id": student_user.id,
                "roll_number": "CS2024001",
                "branch": "Computer Science",
                "year": 2024,
                "cgpa": 8.5,
                "backlog_count": 0,
                "skills": ["Python", "React", "FastAPI", "SQL", "Docker", "TailwindCSS"],
                "phone": "+1-800-555-0101",
                "linkedin_url": "https://linkedin.com/in/alexriver",
            },
            # 2. Top CS Student: 9.4 CGPA, 0 backlogs -> Eligible for all
            {
                "email": "priya.sharma@campushire.demo",
                "full_name": "Priya Sharma",
                "roll_number": "CS2024002",
                "branch": "Computer Science",
                "year": 2024,
                "cgpa": 9.4,
                "backlog_count": 0,
                "skills": ["Python", "PyTorch", "Deep Learning", "TensorFlow", "FastAPI", "Algorithms"],
                "phone": "+1-800-555-0102",
                "linkedin_url": "https://linkedin.com/in/priyasharma-demo",
            },
            # 3. IT Student: 7.8 CGPA, 0 backlogs -> Eligible for SWE & Data Analyst
            {
                "email": "rahul.verma@campushire.demo",
                "full_name": "Rahul Verma",
                "roll_number": "IT2024015",
                "branch": "Information Technology",
                "year": 2024,
                "cgpa": 7.8,
                "backlog_count": 0,
                "skills": ["Java", "Spring Boot", "React", "PostgreSQL", "AWS"],
                "phone": "+1-800-555-0103",
                "linkedin_url": "https://linkedin.com/in/rahulverma-demo",
            },
            # 4. ECE Student: 7.1 CGPA, 1 backlog -> Eligible for Data Analyst & CyberShield (allowing 1 backlog)
            {
                "email": "ananya.iyer@campushire.demo",
                "full_name": "Ananya Iyer",
                "roll_number": "EC2024044",
                "branch": "Electronics",
                "year": 2024,
                "cgpa": 7.1,
                "backlog_count": 1,
                "skills": ["C++", "SQL", "Tableau", "Microcontrollers", "Python"],
                "phone": "+1-800-555-0104",
                "linkedin_url": "https://linkedin.com/in/ananyaiyer-demo",
            },
            # 5. CS Student Batch 2025: 6.8 CGPA, 0 backlogs -> Ineligible for 2024 batch only jobs
            {
                "email": "karthik.nair@campushire.demo",
                "full_name": "Karthik Nair",
                "roll_number": "CS2025088",
                "branch": "Computer Science",
                "year": 2025,
                "cgpa": 6.8,
                "backlog_count": 0,
                "skills": ["JavaScript", "HTML/CSS", "Python", "Git"],
                "phone": "+1-800-555-0105",
                "linkedin_url": "https://linkedin.com/in/karthiknair-demo",
            },
            # 6. Mechanical Student: 8.2 CGPA, 0 backlogs -> Ineligible for CS-only jobs, eligible for open branch drives
            {
                "email": "sneha.patel@campushire.demo",
                "full_name": "Sneha Patel",
                "roll_number": "ME2024012",
                "branch": "Mechanical",
                "year": 2024,
                "cgpa": 8.2,
                "backlog_count": 0,
                "skills": ["CAD/CAM", "MATLAB", "Python", "Thermodynamics", "Analytics"],
                "phone": "+1-800-555-0106",
                "linkedin_url": "https://linkedin.com/in/snehapatel-demo",
            },
            # 7. IT Student with high backlogs / low CGPA: 5.6 CGPA, 3 backlogs -> Ineligible for all high-tier drives
            {
                "email": "rohan.gupta@campushire.demo",
                "full_name": "Rohan Gupta",
                "roll_number": "IT2024099",
                "branch": "Information Technology",
                "year": 2024,
                "cgpa": 5.6,
                "backlog_count": 3,
                "skills": ["PHP", "Basic SQL", "HTML"],
                "phone": "+1-800-555-0107",
                "linkedin_url": "https://linkedin.com/in/rohangupta-demo",
            },
            # 8. ECE Student: 8.8 CGPA, 0 backlogs -> High achiever in electronics & embedded analytics
            {
                "email": "vikram.singh@campushire.demo",
                "full_name": "Vikram Singh",
                "roll_number": "EC2024009",
                "branch": "Electronics",
                "year": 2024,
                "cgpa": 8.8,
                "backlog_count": 0,
                "skills": ["Embedded C", "Python", "Signal Processing", "Data Structures", "Linux"],
                "phone": "+1-800-555-0108",
                "linkedin_url": "https://linkedin.com/in/vikramsingh-demo",
            },
        ]

        students = []
        for cfg in student_configs:
            u_id = cfg.get("user_id")
            if not u_id:
                u = User(
                    email=cfg["email"],
                    hashed_password=DEMO_PASSWORD_HASHED,
                    role=UserRole.STUDENT,
                    full_name=cfg["full_name"],
                    is_active=True,
                )
                db.add(u)
                db.flush()
                u_id = u.id

            student = Student(
                user_id=u_id,
                roll_number=cfg["roll_number"],
                branch=cfg["branch"],
                year=cfg["year"],
                cgpa=cfg["cgpa"],
                backlog_count=cfg["backlog_count"],
                skills=cfg["skills"],
                phone=cfg.get("phone"),
                linkedin_url=cfg.get("linkedin_url"),
            )
            db.add(student)
            students.append(student)

        db.flush()
        print(f"  + Created {len(students)} student profiles with varied branches, CGPAs, and backlogs")

        # =====================================================================
        # 5. Create Resumes
        # =====================================================================
        print("\n[*] Creating verified resume documents...")

        now = datetime.now(timezone.utc)
        resumes = []
        for s in students[:6]:
            resume = Resume(
                student_id=s.id,
                file_path=f"uploads/student_{s.id}_{s.roll_number}_resume.pdf",
                original_filename=f"{s.roll_number}_Resume.pdf",
                is_primary=True,
                uploaded_at=now - timedelta(days=10),
            )
            resumes.append(resume)
            db.add(resume)
        db.flush()
        print(f"  + Created {len(resumes)} student resumes")

        # =====================================================================
        # 6. Create Job Postings (OPEN, DRAFT, CLOSED)
        # =====================================================================
        print("\n[*] Creating job postings across different statuses...")

        jobs = [
            # Job 0: OPEN - Software Engineer (Full Stack)
            Job(
                company_id=companies[0].id,  # TechCorp Solutions
                created_by=recruiter_user.id,
                title="Software Engineer (Full Stack)",
                description="Design and build high-performance web applications, scalable backend microservices with FastAPI and modern React frontends.",
                required_skills=["Python", "JavaScript", "React", "FastAPI", "SQL", "Docker"],
                min_cgpa=7.5,
                eligible_batch=2024,
                allowed_branches=["Computer Science", "Information Technology"],
                maximum_backlogs=0,
                status=JobStatus.OPEN,
                deadline=now + timedelta(days=25),
                package_lpa=12.0,
                employment_type="FULL_TIME",
                location="San Francisco, CA / Hybrid",
            ),
            # Job 1: OPEN - Data Analyst
            Job(
                company_id=companies[1].id,  # DataInsight Analytics
                created_by=recruiter_user_2.id,
                title="Data Analyst",
                description="Extract business intelligence from multi-terabyte datasets, build live executive dashboards, and uncover algorithmic growth trends.",
                required_skills=["SQL", "Python", "Tableau", "Statistics", "Data Visualization"],
                min_cgpa=6.5,
                eligible_batch=2024,
                allowed_branches=["Computer Science", "Information Technology", "Electronics", "Mechanical"],
                maximum_backlogs=1,
                status=JobStatus.OPEN,
                deadline=now + timedelta(days=18),
                package_lpa=8.5,
                employment_type="FULL_TIME",
                location="New York, NY",
            ),
            # Job 2: OPEN - Machine Learning Engineer
            Job(
                company_id=companies[0].id,  # TechCorp Solutions
                created_by=recruiter_user.id,
                title="Machine Learning Engineer",
                description="Develop, train, and deploy production NLP and computer vision neural models on GPU-accelerated clusters.",
                required_skills=["Python", "PyTorch", "TensorFlow", "MLOps", "Deep Learning"],
                min_cgpa=8.0,
                eligible_batch=2024,
                allowed_branches=["Computer Science"],
                maximum_backlogs=0,
                status=JobStatus.OPEN,
                deadline=now + timedelta(days=30),
                package_lpa=16.0,
                employment_type="FULL_TIME",
                location="San Francisco, CA",
            ),
            # Job 3: OPEN - Associate Security Analyst
            Job(
                company_id=companies[3].id,  # CyberShield Security
                created_by=recruiter_user.id,
                title="Associate Security Analyst",
                description="Monitor real-time network traffic anomalies, conduct penetration tests, and automate incident response runbooks.",
                required_skills=["Network Security", "Linux", "Python", "Wireshark", "Vulnerability Assessment"],
                min_cgpa=6.0,
                eligible_batch=2024,
                allowed_branches=["Computer Science", "Information Technology", "Electronics"],
                maximum_backlogs=2,
                status=JobStatus.OPEN,
                deadline=now + timedelta(days=15),
                package_lpa=7.5,
                employment_type="FULL_TIME",
                location="Austin, TX / Remote",
            ),
            # Job 4: DRAFT - Cloud Solutions Architect
            Job(
                company_id=companies[2].id,  # CloudMasters Inc
                created_by=recruiter_user.id,
                title="Cloud Solutions Architect",
                description="Drafting role: Design Kubernetes clusters, automate Terraform provisioning, and manage hybrid cloud infrastructure.",
                required_skills=["Kubernetes", "AWS", "Terraform", "Go", "Docker"],
                min_cgpa=7.0,
                eligible_batch=2024,
                allowed_branches=["Computer Science", "Information Technology"],
                maximum_backlogs=0,
                status=JobStatus.DRAFT,
                deadline=now + timedelta(days=45),
                package_lpa=14.0,
                employment_type="FULL_TIME",
                location="Seattle, WA",
            ),
            # Job 5: CLOSED - QA Automation Engineer
            Job(
                company_id=companies[0].id,  # TechCorp Solutions
                created_by=recruiter_user.id,
                title="QA Automation Engineer",
                description="Recruitment cycle concluded: Automated test frameworks with Playwright and Pytest for web platforms.",
                required_skills=["Python", "Selenium", "Playwright", "CI/CD", "Pytest"],
                min_cgpa=6.5,
                eligible_batch=2024,
                allowed_branches=["Computer Science", "Information Technology", "Electronics"],
                maximum_backlogs=1,
                status=JobStatus.CLOSED,
                deadline=now - timedelta(days=2),
                package_lpa=7.0,
                employment_type="FULL_TIME",
                location="San Francisco, CA",
            ),
        ]
        for job in jobs:
            db.add(job)
        db.flush()
        print(f"  + Created {len(jobs)} job postings (4 OPEN, 1 DRAFT, 1 CLOSED)")

        # =====================================================================
        # 7. Create Applications Across Lifecycle Stages
        # =====================================================================
        print("\n[*] Creating applications spread across all lifecycle stages...")

        # Application 1: Demo student (Alex River) -> Software Engineer (TechCorp) -> SHORTLISTED
        app1 = Application(
            student_id=students[0].id,
            job_id=jobs[0].id,
            resume_id=resumes[0].id,
            status=ApplicationStatus.SHORTLISTED,
            applied_at=now - timedelta(days=4),
        )
        db.add(app1)
        db.flush()

        # Application 2: Top student (Priya Sharma) -> ML Engineer (TechCorp) -> SELECTED
        app2 = Application(
            student_id=students[1].id,
            job_id=jobs[2].id,
            resume_id=resumes[1].id,
            status=ApplicationStatus.SELECTED,
            applied_at=now - timedelta(days=5),
        )
        db.add(app2)
        db.flush()

        # Application 3: IT student (Rahul Verma) -> Software Engineer (TechCorp) -> INTERVIEW_SCHEDULED
        app3 = Application(
            student_id=students[2].id,
            job_id=jobs[0].id,
            resume_id=resumes[2].id,
            status=ApplicationStatus.INTERVIEW_SCHEDULED,
            applied_at=now - timedelta(days=3),
        )
        db.add(app3)
        db.flush()

        # Application 4: ECE student (Ananya Iyer) -> Data Analyst (DataInsight) -> ELIGIBILITY_VERIFIED
        app4 = Application(
            student_id=students[3].id,
            job_id=jobs[1].id,
            resume_id=resumes[3].id,
            status=ApplicationStatus.ELIGIBILITY_VERIFIED,
            applied_at=now - timedelta(days=2),
        )
        db.add(app4)
        db.flush()

        # Application 5: Mechanical student (Sneha Patel) -> Data Analyst (DataInsight) -> SELECTED
        app5 = Application(
            student_id=students[5].id,
            job_id=jobs[1].id,
            resume_id=resumes[5].id,
            status=ApplicationStatus.SELECTED,
            applied_at=now - timedelta(days=4),
        )
        db.add(app5)
        db.flush()

        # Application 6: ECE student (Vikram Singh) -> Associate Security Analyst (CyberShield) -> INTERVIEW
        app6 = Application(
            student_id=students[7].id,
            job_id=jobs[3].id,
            resume_id=None,
            status=ApplicationStatus.INTERVIEW,
            applied_at=now - timedelta(days=3),
        )
        db.add(app6)
        db.flush()

        # Application 7: Demo student (Alex River) -> Data Analyst (DataInsight) -> APPLIED
        app7 = Application(
            student_id=students[0].id,
            job_id=jobs[1].id,
            resume_id=resumes[0].id,
            status=ApplicationStatus.APPLIED,
            applied_at=now - timedelta(hours=8),
        )
        db.add(app7)
        db.flush()

        # Application 8: IT student (Rahul Verma) -> QA Automation (Closed Job) -> REJECTED
        app8 = Application(
            student_id=students[2].id,
            job_id=jobs[5].id,
            resume_id=resumes[2].id,
            status=ApplicationStatus.REJECTED,
            applied_at=now - timedelta(days=12),
        )
        db.add(app8)
        db.flush()

        applications = [app1, app2, app3, app4, app5, app6, app7, app8]

        # Populate realistic audit history for applications
        for app in applications:
            h_applied = ApplicationStatusHistory(
                application_id=app.id,
                old_status=None,
                new_status=ApplicationStatus.APPLIED,
                changed_by=students[0].user_id,
                remarks="Application submitted through student portal",
                changed_at=app.applied_at,
            )
            db.add(h_applied)

            if app.status != ApplicationStatus.APPLIED:
                h_elig = ApplicationStatusHistory(
                    application_id=app.id,
                    old_status=ApplicationStatus.APPLIED,
                    new_status=ApplicationStatus.ELIGIBILITY_VERIFIED,
                    changed_by=None,
                    remarks="Automatic eligibility criteria verified (CGPA, Branch, Backlogs, Batch)",
                    changed_at=app.applied_at + timedelta(minutes=5),
                )
                db.add(h_elig)

            if app.status in [
                ApplicationStatus.SHORTLISTED,
                ApplicationStatus.INTERVIEW_SCHEDULED,
                ApplicationStatus.INTERVIEW,
                ApplicationStatus.SELECTED,
            ]:
                h_short = ApplicationStatusHistory(
                    application_id=app.id,
                    old_status=ApplicationStatus.ELIGIBILITY_VERIFIED,
                    new_status=ApplicationStatus.SHORTLISTED,
                    changed_by=recruiter_user.id,
                    remarks="Profile matched candidate requirements",
                    changed_at=app.applied_at + timedelta(days=1),
                )
                db.add(h_short)

            if app.status in [
                ApplicationStatus.INTERVIEW_SCHEDULED,
                ApplicationStatus.INTERVIEW,
                ApplicationStatus.SELECTED,
            ]:
                h_int_sched = ApplicationStatusHistory(
                    application_id=app.id,
                    old_status=ApplicationStatus.SHORTLISTED,
                    new_status=ApplicationStatus.INTERVIEW_SCHEDULED,
                    changed_by=recruiter_user.id,
                    remarks="Technical Interview round scheduled",
                    changed_at=app.applied_at + timedelta(days=2),
                )
                db.add(h_int_sched)

            if app.status in [ApplicationStatus.INTERVIEW, ApplicationStatus.SELECTED]:
                h_int = ApplicationStatusHistory(
                    application_id=app.id,
                    old_status=ApplicationStatus.INTERVIEW_SCHEDULED,
                    new_status=ApplicationStatus.INTERVIEW,
                    changed_by=recruiter_user.id,
                    remarks="Interview in progress",
                    changed_at=app.applied_at + timedelta(days=3),
                )
                db.add(h_int)

            if app.status == ApplicationStatus.SELECTED:
                h_sel = ApplicationStatusHistory(
                    application_id=app.id,
                    old_status=ApplicationStatus.INTERVIEW,
                    new_status=ApplicationStatus.SELECTED,
                    changed_by=recruiter_user.id,
                    remarks="Offer rolled out after stellar interview rounds",
                    changed_at=app.applied_at + timedelta(days=4),
                )
                db.add(h_sel)

            if app.status == ApplicationStatus.REJECTED:
                h_rej = ApplicationStatusHistory(
                    application_id=app.id,
                    old_status=ApplicationStatus.ELIGIBILITY_VERIFIED,
                    new_status=ApplicationStatus.REJECTED,
                    changed_by=recruiter_user.id,
                    remarks="Position requirements filled by higher match candidates",
                    changed_at=app.applied_at + timedelta(days=6),
                )
                db.add(h_rej)

        db.flush()
        print(f"  + Created {len(applications)} applications with full audit history (APPLIED, SHORTLISTED, INTERVIEW, SELECTED, REJECTED)")

        # =====================================================================
        # 8. Create Interviews
        # =====================================================================
        print("\n[*] Creating interviews across multiple rounds...")

        interviews = [
            # Technical Round for Demo Student (Alex River)
            Interview(
                application_id=app1.id,
                round=InterviewRound.TECHNICAL,
                mode=InterviewMode.ONLINE,
                scheduled_at=now + timedelta(days=4, hours=2),
                location_or_link="https://meet.google.com/abc-demo-tech",
                interviewer="Sarah Jenkins (Lead Architect)",
                notes="Prepare coding round focusing on Python backend and SQL optimization.",
                result=InterviewResult.PENDING,
            ),
            # Completed Tech Round for Priya Sharma (Passed)
            Interview(
                application_id=app2.id,
                round=InterviewRound.TECHNICAL,
                mode=InterviewMode.ONLINE,
                scheduled_at=now - timedelta(days=3),
                location_or_link="https://meet.google.com/xyz-ml-tech",
                interviewer="Dr. David Chen (Principal Scientist)",
                notes="Outstanding mastery of transformer architectures and PyTorch gradient flows.",
                result=InterviewResult.PASSED,
            ),
            # Completed HR Round for Priya Sharma (Passed)
            Interview(
                application_id=app2.id,
                round=InterviewRound.HR,
                mode=InterviewMode.OFFLINE,
                scheduled_at=now - timedelta(days=1),
                location_or_link="Placement Cell Boardroom A",
                interviewer="Jane Smith (HR Lead)",
                notes="Exceptional leadership mindset and seamless cultural alignment.",
                result=InterviewResult.PASSED,
            ),
            # Scheduled Technical Round for Rahul Verma
            Interview(
                application_id=app3.id,
                round=InterviewRound.TECHNICAL,
                mode=InterviewMode.ONLINE,
                scheduled_at=now + timedelta(days=2, hours=4),
                location_or_link="https://teams.microsoft.com/l/meetup-join/demo-rahul",
                interviewer="Elena Rostova (Senior Tech Lead)",
                notes="Focus on Spring Boot microservices and REST API architecture.",
                result=InterviewResult.PENDING,
            ),
            # In-progress Technical Round for Vikram Singh
            Interview(
                application_id=app6.id,
                round=InterviewRound.TECHNICAL,
                mode=InterviewMode.ONLINE,
                scheduled_at=now + timedelta(days=1, hours=3),
                location_or_link="https://cybershield.zoom.us/j/demo-security",
                interviewer="Alan Miller (Security Operations Director)",
                notes="Network security protocols, Wireshark packet capture analysis.",
                result=InterviewResult.PENDING,
            ),
            # Completed Data Analyst Interview for Sneha Patel
            Interview(
                application_id=app5.id,
                round=InterviewRound.ASSESSMENT,
                mode=InterviewMode.ONLINE,
                scheduled_at=now - timedelta(days=2),
                location_or_link="https://datainsight.hackerrank.com/demo-analytics",
                interviewer="Marcus Brody",
                notes="Top 5% score on SQL joins and exploratory statistical analysis.",
                result=InterviewResult.PASSED,
            ),
        ]
        for interview in interviews:
            db.add(interview)
        db.flush()
        print(f"  + Created {len(interviews)} interviews across TECHNICAL, HR, and ASSESSMENT rounds")

        # =====================================================================
        # 9. Create Notifications
        # =====================================================================
        print("\n[*] Creating notifications for students and recruiters...")

        notifications = [
            Notification(
                user_id=student_user.id,
                title="Application Status: Shortlisted!",
                message="Congratulations! Your profile has been shortlisted for Software Engineer (Full Stack) at TechCorp Solutions.",
                is_read=False,
                created_at=now - timedelta(hours=5),
            ),
            Notification(
                user_id=student_user.id,
                title="Upcoming Technical Interview",
                message=f"Technical interview scheduled for Software Engineer on {(now + timedelta(days=4, hours=2)).strftime('%b %d, %Y at %I:%M %p')}. Link: https://meet.google.com/abc-demo-tech",
                is_read=False,
                created_at=now - timedelta(hours=3),
            ),
            Notification(
                user_id=students[1].user_id,
                title="Congratulations - Placement Offer!",
                message="You have been officially selected for the Machine Learning Engineer role at TechCorp Solutions! Welcome aboard.",
                is_read=True,
                created_at=now - timedelta(days=1),
            ),
            Notification(
                user_id=students[2].user_id,
                title="Interview Scheduled",
                message=f"Your technical interview with TechCorp Solutions is confirmed for {(now + timedelta(days=2, hours=4)).strftime('%b %d, %Y at %I:%M %p')}.",
                is_read=False,
                created_at=now - timedelta(hours=8),
            ),
            Notification(
                user_id=recruiter_user.id,
                title="New Student Application Received",
                message="Alex River applied for Software Engineer (Full Stack). Automated eligibility checks passed.",
                is_read=False,
                created_at=now - timedelta(days=4),
            ),
            Notification(
                user_id=recruiter_user.id,
                title="Interview Feedback Recorded",
                message="Technical interview feedback recorded for Priya Sharma (Result: PASSED). Candidate recommended for HR round.",
                is_read=True,
                created_at=now - timedelta(days=2),
            ),
        ]
        for notif in notifications:
            db.add(notif)
        db.flush()
        print(f"  + Created {len(notifications)} notifications")

        # Commit all changes atomically
        db.commit()

        # =====================================================================
        # Summary & Demo Credentials Box
        # =====================================================================
        print("\n" + "=" * 74)
        print("  CAMPUSHIRE DATABASE SEEDED SUCCESSFULLY!  ".center(74))
        print("=" * 74)

        print("\n+------------------------------------------------------------------------+")
        print("|                         DEMO CREDENTIALS                               |")
        print("+------------------------------------------------------------------------+")
        print("|  Role: STUDENT                                                         |")
        print("|    Email:    student@campushire.demo                                   |")
        print("|    Password: DemoPass@123                                              |")
        print("|    Profile:  Alex River (CS, 8.5 CGPA, 0 Backlogs, Shortlisted)        |")
        print("+------------------------------------------------------------------------+")
        print("|  Role: RECRUITER                                                       |")
        print("|    Email:    recruiter@campushire.demo                                 |")
        print("|    Password: DemoPass@123                                              |")
        print("|    Profile:  Jane Smith (TechCorp Solutions - 4 Jobs, Active Pipeline) |")
        print("+------------------------------------------------------------------------+")
        print("|  Role: PLACEMENT OFFICER                                               |")
        print("|    Email:    placement@campushire.demo                                 |")
        print("|    Password: DemoPass@123                                              |")
        print("|    Profile:  Dr. Arthur Vance (Placement Cell Admin Dashboard & Reports)|")
        print("+------------------------------------------------------------------------+")

        print("\n[*] SEEDED DATA SUMMARY:")
        print(f"  - {len(companies)} Partner Companies (TechCorp, DataInsight, CloudMasters, CyberShield)")
        print(f"  - {len(students)} Student Profiles (Varied Branches: CS, IT, ECE, Mech; CGPA: 5.6 to 9.4)")
        print(f"  - {len(jobs)} Job Postings (OPEN, DRAFT, CLOSED with criteria boundaries)")
        print(f"  - {len(applications)} Candidate Applications (APPLIED, SHORTLISTED, INTERVIEW, SELECTED, REJECTED)")
        print(f"  - {len(interviews)} Interview Rounds (Technical, HR, Assessment)")
        print(f"  - {len(notifications)} Notifications with real-time counters")
        print("\n" + "=" * 74 + "\n")

    except Exception as e:
        db.rollback()
        print(f"\n[!] Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    print("\n[*] Initializing CampusHire Demo Database Seeder...")
    print("=" * 74)
    seed_database()
