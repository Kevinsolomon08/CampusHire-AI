# tests/test_eligibility_service.py
from types import SimpleNamespace
import pytest
from app.services.eligibility_service import check_eligibility


class MockStudent:
    def __init__(self, cgpa=None, department=None, backlog_count=None, batch=None, branch=None, year=None):
        self.cgpa = cgpa
        self.department = department or branch
        self.backlog_count = backlog_count
        self.batch = batch or year


class MockJob:
    def __init__(self, minimum_cgpa=None, allowed_branches=None, maximum_backlogs=None, eligible_batch=None):
        self.minimum_cgpa = minimum_cgpa
        self.allowed_branches = allowed_branches
        self.maximum_backlogs = maximum_backlogs
        self.eligible_batch = eligible_batch


def test_eligible_student_all_pass():
    student = MockStudent(cgpa=8.5, department="CSE", backlog_count=0, batch=2025)
    job = MockJob(minimum_cgpa=7.5, allowed_branches=["CSE", "IT"], maximum_backlogs=0, eligible_batch=2025)

    result = check_eligibility(student, job)
    assert result == {"eligible": True, "reasons": []}


def test_cgpa_failure_exact_message():
    student = MockStudent(cgpa=6.8, department="CSE", backlog_count=0, batch=2025)
    job = MockJob(minimum_cgpa=7.5, allowed_branches=["CSE"], maximum_backlogs=1, eligible_batch=2025)

    result = check_eligibility(student, job)
    assert result["eligible"] is False
    assert result["reasons"] == [
        "Minimum CGPA requirement is 7.5. Your CGPA is 6.8."
    ]


def test_branch_failure_exact_message():
    student = MockStudent(cgpa=8.5, department="MECH", backlog_count=0, batch=2025)
    job = MockJob(minimum_cgpa=7.0, allowed_branches=["CSE", "ECE"], maximum_backlogs=0, eligible_batch=2025)

    result = check_eligibility(student, job)
    assert result["eligible"] is False
    assert result["reasons"] == [
        "This job is open to ['CSE', 'ECE'] only. Your branch is MECH."
    ]


def test_backlogs_failure_exact_message():
    student = MockStudent(cgpa=8.5, department="CSE", backlog_count=2, batch=2025)
    job = MockJob(minimum_cgpa=7.0, allowed_branches=["CSE"], maximum_backlogs=1, eligible_batch=2025)

    result = check_eligibility(student, job)
    assert result["eligible"] is False
    assert result["reasons"] == [
        "Maximum allowed backlogs is 1. You have 2."
    ]


def test_batch_failure_exact_message():
    student = MockStudent(cgpa=8.5, department="CSE", backlog_count=0, batch=2024)
    job = MockJob(minimum_cgpa=7.0, allowed_branches=["CSE"], maximum_backlogs=0, eligible_batch=2025)

    result = check_eligibility(student, job)
    assert result["eligible"] is False
    assert result["reasons"] == [
        "This job is open to the 2025 batch. Your batch is 2024."
    ]


def test_multiple_failures_collected_in_exact_order():
    student = MockStudent(cgpa=6.2, department="CIVIL", backlog_count=3, batch=2023)
    job = MockJob(minimum_cgpa=7.5, allowed_branches=["CSE", "IT"], maximum_backlogs=1, eligible_batch=2025)

    result = check_eligibility(student, job)
    assert result["eligible"] is False
    assert len(result["reasons"]) == 4
    assert result["reasons"][0] == "Minimum CGPA requirement is 7.5. Your CGPA is 6.2."
    assert result["reasons"][1] == "This job is open to ['CSE', 'IT'] only. Your branch is CIVIL."
    assert result["reasons"][2] == "Maximum allowed backlogs is 1. You have 3."
    assert result["reasons"][3] == "This job is open to the 2025 batch. Your batch is 2023."


def test_with_dictionaries():
    student_dict = {
        "cgpa": 7.0,
        "department": "ECE",
        "backlog_count": 0,
        "batch": 2025
    }
    job_dict = {
        "minimum_cgpa": 7.5,
        "allowed_branches": ["ECE"],
        "maximum_backlogs": 0,
        "eligible_batch": 2025
    }
    result = check_eligibility(student_dict, job_dict)
    assert result["eligible"] is False
    assert result["reasons"] == ["Minimum CGPA requirement is 7.5. Your CGPA is 7.0."]


def test_with_partial_requirements_none():
    student = MockStudent(cgpa=6.0, department="EEE", backlog_count=2, batch=2026)
    # Job has no restrictions
    job = MockJob()

    result = check_eligibility(student, job)
    assert result == {"eligible": True, "reasons": []}


def test_unverified_cgpa_when_cutoff_required():
    student = MockStudent(cgpa=None, department="CSE", backlog_count=0, batch=2025)
    job = MockJob(minimum_cgpa=7.5, allowed_branches=["CSE"], maximum_backlogs=0, eligible_batch=2025)

    result = check_eligibility(student, job)
    assert result["eligible"] is False
    assert result["reasons"] == [
        "Your CGPA hasn't been verified yet. Please upload your marksheet in your profile."
    ]


def test_unverified_cgpa_when_no_cgpa_required():
    student = MockStudent(cgpa=None, department="CSE", backlog_count=0, batch=2025)
    job = MockJob(minimum_cgpa=None, allowed_branches=["CSE"], maximum_backlogs=0, eligible_batch=2025)

    result = check_eligibility(student, job)
    assert result["eligible"] is True
    assert result["reasons"] == []


def test_unverified_cgpa_with_dictionary_payload():
    student_dict = {"cgpa": None, "department": "ECE", "backlog_count": 0, "batch": 2025}
    job_dict = {"minimum_cgpa": 6.5, "allowed_branches": ["ECE"], "maximum_backlogs": 0, "eligible_batch": 2025}

    result = check_eligibility(student_dict, job_dict)
    assert result["eligible"] is False
    assert result["reasons"] == [
        "Your CGPA hasn't been verified yet. Please upload your marksheet in your profile."
    ]
