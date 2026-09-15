# app/services/application_service.py
"""
CampusHire Application Status Service.

Provides pure, stateless helpers for managing application status transitions
and shaping ApplicationStatusHistory records.  Neither function touches the
database – that is the responsibility of the calling route/service layer.
"""

from datetime import datetime, timezone
from typing import Optional

# ---------------------------------------------------------------------------
# State diagram (plain-text reference)
#
#   APPLIED
#     └─► ELIGIBILITY_VERIFIED
#           └─► SHORTLISTED
#                 └─► INTERVIEW_SCHEDULED
#                       └─► INTERVIEW
#                             ├─► SELECTED
#                             └─► REJECTED
#
# Terminal states:  SELECTED, REJECTED
#
# Reopen exception (PLACEMENT_OFFICER only):
#   SELECTED  ──► ELIGIBILITY_VERIFIED   (reason: "Reopened by placement officer")
#   REJECTED  ──► ELIGIBILITY_VERIFIED   (reason: "Reopened by placement officer")
#
# All other backward / sideways / skip transitions are disallowed for every role.
# Same-status transitions are always disallowed.
# ---------------------------------------------------------------------------

# The ordered forward-transition map: current -> allowed next state(s)
_FORWARD_TRANSITIONS: dict[str, set[str]] = {
    "APPLIED":              {"ELIGIBILITY_VERIFIED"},
    "ELIGIBILITY_VERIFIED": {"SHORTLISTED"},
    "SHORTLISTED":          {"INTERVIEW_SCHEDULED"},
    "INTERVIEW_SCHEDULED":  {"INTERVIEW"},
    "INTERVIEW":            {"SELECTED", "REJECTED"},
    # Terminal states – no forward transitions
    "SELECTED":             set(),
    "REJECTED":             set(),
}

# States that a PLACEMENT_OFFICER may reopen back to ELIGIBILITY_VERIFIED
_REOPEN_SOURCES: set[str] = {"SELECTED", "REJECTED"}
_REOPEN_TARGET: str = "ELIGIBILITY_VERIFIED"


def validate_status_transition(
    current_status: str,
    new_status: str,
    actor_role: str,
) -> dict:
    """
    Validate whether moving an application from *current_status* to *new_status*
    is permitted for the given *actor_role*.

    Returns:
        {
            "allowed": bool,
            "reason":  str | None   # None when allowed=True (except reopen)
        }

    Rules (evaluated in order):
    1. Same-status is always rejected.
    2. Any forward transition listed in _FORWARD_TRANSITIONS is allowed for all roles.
    3. A PLACEMENT_OFFICER may reopen SELECTED or REJECTED back to ELIGIBILITY_VERIFIED.
    4. Everything else is rejected with an explanatory message.
    """
    # 1. No-op guard
    if current_status == new_status:
        return {
            "allowed": False,
            "reason": "Application is already in this status.",
        }

    # 2. Valid forward transition (any role)
    allowed_next = _FORWARD_TRANSITIONS.get(current_status, set())
    if new_status in allowed_next:
        return {"allowed": True, "reason": None}

    # 3. Placement-officer reopen exception
    if (
        actor_role == "PLACEMENT_OFFICER"
        and current_status in _REOPEN_SOURCES
        and new_status == _REOPEN_TARGET
    ):
        return {"allowed": True, "reason": "Reopened by placement officer"}

    # 4. Everything else is disallowed
    return {
        "allowed": False,
        "reason": (
            f"Cannot move application from {current_status} to {new_status}: "
            "this transition is not permitted."
        ),
    }


def build_status_history_entry(
    application_id: int,
    old_status: str,
    new_status: str,
    changed_by_user_id: int,
    remarks: Optional[str] = None,
) -> dict:
    """
    Shape a dict suitable for inserting as an ApplicationStatusHistory row.

    This function is intentionally side-effect-free: it does not write to the
    database.  The route layer is responsible for persisting the returned dict.

    Returns:
        {
            "application_id":    int,
            "old_status":        str,
            "new_status":        str,
            "changed_by_user_id": int,
            "remarks":           str | None,
            "changed_at":        datetime (UTC, timezone-aware),
        }
    """
    return {
        "application_id": application_id,
        "old_status": old_status,
        "new_status": new_status,
        "changed_by_user_id": changed_by_user_id,
        "remarks": remarks,
        "changed_at": datetime.now(tz=timezone.utc),
    }
