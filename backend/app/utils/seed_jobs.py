# app/utils/seed_jobs.py
"""
Seeds sample company and job records in the database for testing and demonstration.
"""

from datetime import datetime, timedelta
from app.database.connection import SessionLocal
from app.models.models import Company, Job, JobStatus, User, UserRole
from app.core.security import hash_password


def seed_data():
    db = SessionLocal()
    try:
        # 1. Ensure a recruiter/company user exists
        recruiter_user = db.query(User).filter(User.email == "recruiter@google.com").first()
        if not recruiter_user:
            recruiter_user = User(
                email="recruiter@google.com",
                hashed_password=hash_password("Password123!"),
                role=UserRole.RECRUITER,
                full_name="Sarah Jenkins",
                is_active=True,
            )
            db.add(recruiter_user)
            db.commit()
            db.refresh(recruiter_user)

        # 2. Ensure companies exist
        google = db.query(Company).filter(Company.name == "Google").first()
        if not google:
            google = Company(
                name="Google",
                website="https://careers.google.com",
                industry="Software & Internet",
                description="Google is a global technology leader focused on improving the ways people connect with information.",
                logo_url="https://www.google.com/favicon.ico",
            )
            db.add(google)
            db.commit()
            db.refresh(google)

        microsoft = db.query(Company).filter(Company.name == "Microsoft").first()
        if not microsoft:
            microsoft = Company(
                name="Microsoft",
                website="https://careers.microsoft.com",
                industry="Cloud & Enterprise Software",
                description="Microsoft enables digital transformation for the era of an intelligent cloud and an intelligent edge.",
                logo_url="https://www.microsoft.com/favicon.ico",
            )
            db.add(microsoft)
            db.commit()
            db.refresh(microsoft)

        amazon = db.query(Company).filter(Company.name == "Amazon").first()
        if not amazon:
            amazon = Company(
                name="Amazon",
                website="https://amazon.jobs",
                industry="E-Commerce & Cloud",
                description="Amazon is guided by four principles: customer obsession, passion for invention, commitment to operational excellence, and long-term thinking.",
                logo_url="https://www.amazon.com/favicon.ico",
            )
            db.add(amazon)
            db.commit()
            db.refresh(amazon)

        # 3. Create Sample Jobs with different eligibility criteria if not present
        existing_jobs_count = db.query(Job).count()
        if existing_jobs_count == 0:
            sample_jobs = [
                Job(
                    company_id=google.id,
                    created_by=recruiter_user.id,
                    title="Software Engineer - University Graduate",
                    description="Join Google as a Software Engineer and work on core systems, large-scale search infrastructure, and cutting-edge machine learning applications.",
                    location="Bangalore / Hyderabad, India",
                    package_lpa=24.0,
                    min_cgpa=8.0,
                    allowed_branches=["Computer Science", "CSE", "Information Technology", "IT"],
                    maximum_backlogs=0,
                    eligible_batch=2025,
                    requirements=["Strong DSA foundations", "Proficiency in C++, Java or Python", "System design basics"],
                    required_skills=["Python", "C++", "Algorithms", "Data Structures"],
                    status=JobStatus.OPEN,
                    deadline=datetime.utcnow() + timedelta(days=30),
                ),
                Job(
                    company_id=microsoft.id,
                    created_by=recruiter_user.id,
                    title="Associate Cloud Solution Architect",
                    description="Help enterprise customers transform their business using Microsoft Azure cloud platform, microservices, and AI integrations.",
                    location="Hyderabad / Noida, India",
                    package_lpa=18.5,
                    min_cgpa=7.0,
                    allowed_branches=["Computer Science", "CSE", "ECE", "Information Technology", "IT"],
                    maximum_backlogs=1,
                    eligible_batch=2025,
                    requirements=["Understanding of Cloud Computing & Networking", "Good problem solving", "Excellent communication"],
                    required_skills=["Azure", "Cloud Computing", "Python", "Networking"],
                    status=JobStatus.OPEN,
                    deadline=datetime.utcnow() + timedelta(days=45),
                ),
                Job(
                    company_id=amazon.id,
                    created_by=recruiter_user.id,
                    title="SDE-1 (Frontend & Fullstack)",
                    description="Build delightful customer-facing shopping experiences powering millions of daily interactions across Amazon web and mobile platforms.",
                    location="Bangalore, India",
                    package_lpa=22.0,
                    min_cgpa=6.5,
                    allowed_branches=["Computer Science", "CSE", "ECE", "EEE", "Information Technology", "IT", "Mechanical"],
                    maximum_backlogs=0,
                    eligible_batch=2025,
                    requirements=["Strong JavaScript/TypeScript & React", "HTML5/CSS3 mastery", "REST APIs"],
                    required_skills=["React", "JavaScript", "TypeScript", "Node.js"],
                    status=JobStatus.OPEN,
                    deadline=datetime.utcnow() + timedelta(days=20),
                ),
                Job(
                    company_id=google.id,
                    created_by=recruiter_user.id,
                    title="AI/ML Research Intern",
                    description="Research next-generation LLM architectures, diffusion models, and multimodal perception systems.",
                    location="Bangalore, India",
                    package_lpa=30.0,
                    min_cgpa=9.0,
                    allowed_branches=["Computer Science", "CSE"],
                    maximum_backlogs=0,
                    eligible_batch=2026,
                    requirements=["Published papers or deep learning projects", "PyTorch / JAX experience", "Strong math background"],
                    required_skills=["PyTorch", "Deep Learning", "Python", "Linear Algebra"],
                    status=JobStatus.OPEN,
                    deadline=datetime.utcnow() + timedelta(days=15),
                ),
            ]
            db.add_all(sample_jobs)
            db.commit()
            print(f"Successfully seeded {len(sample_jobs)} sample jobs!")
        else:
            print(f"Jobs already exist ({existing_jobs_count} found).")

    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
