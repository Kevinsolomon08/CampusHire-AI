# tests/test_application_service.py
"""
Tests for app/services/application_service.py.

Coverage matrix
---------------
validate_status_transition
  Forward transitions (all 6 edges) — allowed=True
  ├─ APPLIED              -> ELIGIBILITY_VERIFIED
  ├─ ELIGIBILITY_VERIFIED -> SHORTLISTED
  ├─ SHORTLISTED          -> INTERVIEW_SCHEDULED
  ├─ INTERVIEW_SCHEDULED  -> INTERVIEW
  ├─ INTERVIEW            -> SELECTED
  └─ INTERVIEW            -> REJECTED

  Invalid transitions — allowed=False
  ├─ REJECTED   -> INTERVIEW  (backward, RECRUITER)          [required #2]
  ├─ APPLIED    -> SELECTED   (skip stages)                  [required #3]
  ├─ SHORTLISTED -> SHORTLISTED (no-op / same status)        [required #4]
  ├─ SELECTED   -> ELIGIBILITY_VERIFIED (RECRUITER)          [required #6]
  ├─ Any terminal -> forward (e.g. SELECTED -> INTERVIEW)
  ├─ Backward non-terminal (e.g. SHORTLISTED -> APPLIED)
  └─ Completely arbitrary strings

  Placement-officer reopen — allowed=True + reason string
  ├─ SELECTED -> ELIGIBILITY_VERIFIED  (PLACEMENT_OFFICER)   [required #5]
  └─ REJECTED -> ELIGIBILITY_VERIFIED  (PLACEMENT_OFFICER)   [required #7]

  Placement-officer reopen blocked for wrong target
  └─ SELECTED -> SHORTLISTED           (PLACEMENT_OFFICER)

build_status_history_entry
  ├─ All fields present in returned dict
  ├─ Optional remarks=None is preserved
  ├─ changed_at is a timezone-aware UTC datetime
  └─ Values passed through unchanged
"""

from datetime import datetime, timezone

import pytest

from app.services.application_service import (
    build_status_history_entry,
    validate_status_transition,
)

# ---------------------------------------------------------------------------
# Helpers / constants
# ---------------------------------------------------------------------------

RECRUITER = "RECRUITER"
PLACEMENT_OFFICER = "PLACEMENT_OFFICER"
STUDENT = "STUDENT"  # role that should never be able to override


# ---------------------------------------------------------------------------
# Forward transitions — all six edges must be allowed for any role
# ---------------------------------------------------------------------------


def test_forward_applied_to_eligibility_verified():
    result = validate_status_transition("APPLIED", "ELIGIBILITY_VERIFIED", RECRUITER)
    assert result["allowed"] is True
    assert result["reason"] is None


def test_forward_eligibility_verified_to_shortlisted():
    result = validate_status_transition("ELIGIBILITY_VERIFIED", "SHORTLISTED", RECRUITER)
    assert result["allowed"] is True
    assert result["reason"] is None


def test_forward_shortlisted_to_interview_scheduled():
    result = validate_status_transition("SHORTLISTED", "INTERVIEW_SCHEDULED", RECRUITER)
    assert result["allowed"] is True
    assert result["reason"] is None


def test_forward_interview_scheduled_to_interview():
    result = validate_status_transition("INTERVIEW_SCHEDULED", "INTERVIEW", RECRUITER)
    assert result["allowed"] is True
    assert result["reason"] is None


def test_forward_interview_to_selected():
    result = validate_status_transition("INTERVIEW", "SELECTED", RECRUITER)
    assert result["allowed"] is True
    assert result["reason"] is None


def test_forward_interview_to_rejected():
    result = validate_status_transition("INTERVIEW", "REJECTED", RECRUITER)
    assert result["allowed"] is True
    assert result["reason"] is None


# Forward transitions work for PLACEMENT_OFFICER too
def test_forward_transitions_also_allowed_for_placement_officer():
    result = validate_status_transition("APPLIED", "ELIGIBILITY_VERIFIED", PLACEMENT_OFFICER)
    assert result["allowed"] is True
    assert result["reason"] is None


# ---------------------------------------------------------------------------
# Required case #2: backward transition by RECRUITER
# ---------------------------------------------------------------------------


def test_rejected_to_interview_by_recruiter_not_allowed():
    result = validate_status_transition("REJECTED", "INTERVIEW", RECRUITER)
    assert result["allowed"] is False
    assert result["reason"] is not None
    assert "REJECTED" in result["reason"]
    assert "INTERVIEW" in result["reason"]


# ---------------------------------------------------------------------------
# Required case #3: skipping stages
# ---------------------------------------------------------------------------


def test_applied_to_selected_skip_stages_not_allowed():
    result = validate_status_transition("APPLIED", "SELECTED", RECRUITER)
    assert result["allowed"] is False
    assert result["reason"] is not None
    assert "APPLIED" in result["reason"]
    assert "SELECTED" in result["reason"]


# ---------------------------------------------------------------------------
# Required case #4: same-status no-op
# ---------------------------------------------------------------------------


def test_shortlisted_to_shortlisted_not_allowed():
    result = validate_status_transition("SHORTLISTED", "SHORTLISTED", RECRUITER)
    assert result["allowed"] is False
    assert result["reason"] == "Application is already in this status."


# Also verify the no-op message for every other status
@pytest.mark.parametrize("status", [
    "APPLIED",
    "ELIGIBILITY_VERIFIED",
    "INTERVIEW_SCHEDULED",
    "INTERVIEW",
    "SELECTED",
    "REJECTED",
])
def test_same_status_always_not_allowed(status):
    result = validate_status_transition(status, status, RECRUITER)
    assert result["allowed"] is False
    assert result["reason"] == "Application is already in this status."


# ---------------------------------------------------------------------------
# Required case #5: PLACEMENT_OFFICER reopen SELECTED -> ELIGIBILITY_VERIFIED
# ---------------------------------------------------------------------------


def test_selected_to_eligibility_verified_by_placement_officer_allowed():
    result = validate_status_transition("SELECTED", "ELIGIBILITY_VERIFIED", PLACEMENT_OFFICER)
    assert result["allowed"] is True
    assert result["reason"] == "Reopened by placement officer"


# ---------------------------------------------------------------------------
# Required case #6: RECRUITER cannot reopen
# ---------------------------------------------------------------------------


def test_selected_to_eligibility_verified_by_recruiter_not_allowed():
    result = validate_status_transition("SELECTED", "ELIGIBILITY_VERIFIED", RECRUITER)
    assert result["allowed"] is False
    assert result["reason"] is not None
    assert "SELECTED" in result["reason"]
    assert "ELIGIBILITY_VERIFIED" in result["reason"]


# ---------------------------------------------------------------------------
# Required case #7: PLACEMENT_OFFICER reopen REJECTED -> ELIGIBILITY_VERIFIED
# ---------------------------------------------------------------------------


def test_rejected_to_eligibility_verified_by_placement_officer_allowed():
    result = validate_status_transition("REJECTED", "ELIGIBILITY_VERIFIED", PLACEMENT_OFFICER)
    assert result["allowed"] is True
    assert result["reason"] == "Reopened by placement officer"


# ---------------------------------------------------------------------------
# Additional invalid-transition coverage
# ---------------------------------------------------------------------------


def test_terminal_selected_cannot_move_forward():
    """SELECTED has no forward transitions; even INTERVIEW should be blocked."""
    result = validate_status_transition("SELECTED", "INTERVIEW", RECRUITER)
    assert result["allowed"] is False
    assert "SELECTED" in result["reason"]


def test_terminal_rejected_cannot_move_forward():
    result = validate_status_transition("REJECTED", "SELECTED", RECRUITER)
    assert result["allowed"] is False
    assert "REJECTED" in result["reason"]


def test_backward_non_terminal_shortlisted_to_applied():
    result = validate_status_transition("SHORTLISTED", "APPLIED", RECRUITER)
    assert result["allowed"] is False
    assert "SHORTLISTED" in result["reason"]
    assert "APPLIED" in result["reason"]


def test_placement_officer_reopen_to_wrong_target_not_allowed():
    """PLACEMENT_OFFICER reopen only goes back to ELIGIBILITY_VERIFIED, not elsewhere."""
    result = validate_status_transition("SELECTED", "SHORTLISTED", PLACEMENT_OFFICER)
    assert result["allowed"] is False


def test_placement_officer_cannot_skip_stages_forward():
    """Placement officer gets no special privilege for forward skips."""
    result = validate_status_transition("APPLIED", "SHORTLISTED", PLACEMENT_OFFICER)
    assert result["allowed"] is False


def test_invalid_status_strings_rejected():
    result = validate_status_transition("UNKNOWN_STATE", "SELECTED", RECRUITER)
    assert result["allowed"] is False


def test_student_role_cannot_reopen():
    result = validate_status_transition("REJECTED", "ELIGIBILITY_VERIFIED", STUDENT)
    assert result["allowed"] is False


def test_interview_scheduled_cannot_jump_to_selected():
    result = validate_status_transition("INTERVIEW_SCHEDULED", "SELECTED", RECRUITER)
    assert result["allowed"] is False


def test_eligibility_verified_cannot_go_back_to_applied():
    result = validate_status_transition("ELIGIBILITY_VERIFIED", "APPLIED", RECRUITER)
    assert result["allowed"] is False


# ---------------------------------------------------------------------------
# build_status_history_entry
# ---------------------------------------------------------------------------


def test_build_status_history_entry_all_fields_present():
    entry = build_status_history_entry(
        application_id=42,
        old_status="APPLIED",
        new_status="ELIGIBILITY_VERIFIED",
        changed_by_user_id=7,
        remarks="Verified by placement cell",
    )
    assert entry["application_id"] == 42
    assert entry["old_status"] == "APPLIED"
    assert entry["new_status"] == "ELIGIBILITY_VERIFIED"
    assert entry["changed_by_user_id"] == 7
    assert entry["remarks"] == "Verified by placement cell"
    assert "changed_at" in entry


def test_build_status_history_entry_remarks_none():
    entry = build_status_history_entry(
        application_id=1,
        old_status="INTERVIEW",
        new_status="SELECTED",
        changed_by_user_id=3,
        remarks=None,
    )
    assert entry["remarks"] is None


def test_build_status_history_entry_changed_at_is_utc_aware():
    entry = build_status_history_entry(
        application_id=5,
        old_status="SHORTLISTED",
        new_status="INTERVIEW_SCHEDULED",
        changed_by_user_id=10,
    )
    changed_at = entry["changed_at"]
    assert isinstance(changed_at, datetime)
    # Must be timezone-aware
    assert changed_at.tzinfo is not None
    assert changed_at.tzinfo == timezone.utc


def test_build_status_history_entry_changed_at_is_recent():
    before = datetime.now(tz=timezone.utc)
    entry = build_status_history_entry(
        application_id=99,
        old_status="INTERVIEW",
        new_status="REJECTED",
        changed_by_user_id=2,
    )
    after = datetime.now(tz=timezone.utc)
    assert before <= entry["changed_at"] <= after


def test_build_status_history_entry_values_pass_through_unchanged():
    entry = build_status_history_entry(
        application_id=0,
        old_status="SELECTED",
        new_status="ELIGIBILITY_VERIFIED",
        changed_by_user_id=999,
        remarks="Reopened",
    )
    assert entry["application_id"] == 0
    assert entry["old_status"] == "SELECTED"
    assert entry["new_status"] == "ELIGIBILITY_VERIFIED"
    assert entry["changed_by_user_id"] == 999
    assert entry["remarks"] == "Reopened"
