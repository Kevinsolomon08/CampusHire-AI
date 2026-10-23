# app/services/eligibility_service.py
"""
CampusHire Student Eligibility Service.

Evaluates whether a student meets the requirements set for a specific job posting.
Checks the following rules in strict order, accumulating all failure reasons:
1. CGPA: student.cgpa >= job.minimum_cgpa
2. Branch / Department: student.department in job.allowed_branches
3. Backlogs: student.backlog_count <= job.maximum_backlogs
4. Batch: student.batch == job.eligible_batch
"""

from typing import Any, Dict, List, Optional, Union


def _get_val(obj: Any, *keys: str, default: Any = None) -> Any:
    """Helper to safely extract attribute or dict item from student or job object."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        for k in keys:
            if k in obj and obj[k] is not None:
                return obj[k]
        return default
    for k in keys:
        if hasattr(obj, k):
            val = getattr(obj, k)
            if val is not None:
                return val
    return default


def check_eligibility(student: Any, job: Any) -> Dict[str, Union[bool, List[str]]]:
    """
    Check whether a student is eligible for a given job.

    Returns:
        {
            "eligible": bool,
            "reasons": [str, ...]
        }
    """
    reasons: List[str] = []

    # 1. CGPA check
    minimum_cgpa = _get_val(job, "minimum_cgpa", "min_cgpa")
    student_cgpa = _get_val(student, "cgpa", "student_cgpa")
    if minimum_cgpa is not None:
        if student_cgpa is None:
            reasons.append("Your CGPA hasn't been verified yet. Please upload your marksheet in your profile.")
        elif student_cgpa < minimum_cgpa:
            reasons.append(
                f"Minimum CGPA requirement is {minimum_cgpa}. Your CGPA is {student_cgpa}."
            )

    # 2. Branch / Department check
    allowed_branches = _get_val(job, "allowed_branches", "branches", "departments")
    student_department = _get_val(student, "department", "branch", "dept")
    if allowed_branches is not None:
        is_branch_allowed = False
        if student_department is not None:
            if isinstance(allowed_branches, (list, tuple, set)):
                is_branch_allowed = student_department in allowed_branches
            elif isinstance(allowed_branches, str):
                parsed = [b.strip() for b in allowed_branches.split(",") if b.strip()]
                is_branch_allowed = (student_department in parsed) or (student_department == allowed_branches)
        if not is_branch_allowed:
            reasons.append(
                f"This job is open to {allowed_branches} only. Your branch is {student_department}."
            )

    # 3. Backlogs check
    maximum_backlogs = _get_val(job, "maximum_backlogs", "max_backlogs")
    student_backlog_count = _get_val(student, "backlog_count", "backlogs", "student_backlog_count")
    if maximum_backlogs is not None:
        current_backlogs = student_backlog_count if student_backlog_count is not None else 0
        if current_backlogs > maximum_backlogs:
            reasons.append(
                f"Maximum allowed backlogs is {maximum_backlogs}. You have {student_backlog_count}."
            )

    # 4. Batch check
    eligible_batch = _get_val(job, "eligible_batch", "batch", "year")
    student_batch = _get_val(student, "batch", "year", "student_batch")
    if eligible_batch is not None:
        # Compare as equality (supporting int and str representations)
        if student_batch != eligible_batch and str(student_batch) != str(eligible_batch):
            reasons.append(
                f"This job is open to the {eligible_batch} batch. Your batch is {student_batch}."
            )

    return {
        "eligible": len(reasons) == 0,
        "reasons": reasons,
    }
