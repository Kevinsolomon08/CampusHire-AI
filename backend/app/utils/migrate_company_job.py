# app/utils/migrate_company_job.py
from app.database.connection import engine
from sqlalchemy import text, inspect

def migrate():
    insp = inspect(engine)
    company_cols = [c['name'] for c in insp.get_columns('companies')]
    job_cols = [c['name'] for c in insp.get_columns('jobs')]

    with engine.connect() as conn:
        if 'contact_email' not in company_cols:
            conn.execute(text("ALTER TABLE companies ADD COLUMN contact_email VARCHAR(255) NULL"))
        if 'contact_phone' not in company_cols:
            conn.execute(text("ALTER TABLE companies ADD COLUMN contact_phone VARCHAR(50) NULL"))
        if 'address' not in company_cols:
            conn.execute(text("ALTER TABLE companies ADD COLUMN address VARCHAR(500) NULL"))

        if 'preferred_skills' not in job_cols:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN preferred_skills JSON NULL"))
        if 'experience_requirement' not in job_cols:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN experience_requirement VARCHAR(100) NULL"))
        if 'employment_type' not in job_cols:
            conn.execute(text("ALTER TABLE jobs ADD COLUMN employment_type VARCHAR(50) NOT NULL DEFAULT 'FULL_TIME'"))

        conn.commit()
        print("Company and Job columns successfully added to DB!")

if __name__ == "__main__":
    migrate()
