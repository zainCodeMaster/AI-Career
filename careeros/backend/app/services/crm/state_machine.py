"""Application lifecycle state machine for Phase 7 CRM."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional, Set

from app.db.models.crm import ApplicationStatus


# ---------------------------------------------------------------------------
# State transition rules
# ---------------------------------------------------------------------------

# Legal transitions from each state.
# Additive only: never remove values, only deprecate.
_ALLOWED_TRANSITIONS: dict[ApplicationStatus, Set[ApplicationStatus]] = {
    ApplicationStatus.SAVED: {
        ApplicationStatus.READY_TO_APPLY,
        ApplicationStatus.APPLIED,
        ApplicationStatus.ON_HOLD,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.READY_TO_APPLY: {
        ApplicationStatus.APPLIED,
        ApplicationStatus.SAVED,
        ApplicationStatus.ON_HOLD,
        ApplicationStatus.WITHDRAWN,
    },
    ApplicationStatus.APPLIED: {
        ApplicationStatus.APPLICATION_VIEWED,
        ApplicationStatus.SCREENING,
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
        ApplicationStatus.ON_HOLD,
        ApplicationStatus.EXPIRED,
    },
    ApplicationStatus.APPLICATION_VIEWED: {
        ApplicationStatus.SCREENING,
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
        ApplicationStatus.ON_HOLD,
    },
    ApplicationStatus.SCREENING: {
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.TECHNICAL_INTERVIEW,
        ApplicationStatus.FINAL_INTERVIEW,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
        ApplicationStatus.ON_HOLD,
    },
    ApplicationStatus.INTERVIEW: {
        ApplicationStatus.TECHNICAL_INTERVIEW,
        ApplicationStatus.FINAL_INTERVIEW,
        ApplicationStatus.OFFER,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
        ApplicationStatus.ON_HOLD,
    },
    ApplicationStatus.TECHNICAL_INTERVIEW: {
        ApplicationStatus.FINAL_INTERVIEW,
        ApplicationStatus.OFFER,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
        ApplicationStatus.ON_HOLD,
    },
    ApplicationStatus.FINAL_INTERVIEW: {
        ApplicationStatus.OFFER,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
        ApplicationStatus.ON_HOLD,
    },
    ApplicationStatus.OFFER: {
        ApplicationStatus.ACCEPTED,
        ApplicationStatus.REJECTED,
        ApplicationStatus.WITHDRAWN,
        ApplicationStatus.ON_HOLD,
    },
    ApplicationStatus.ACCEPTED: set(),
    ApplicationStatus.REJECTED: set(),
    ApplicationStatus.WITHDRAWN: set(),
    ApplicationStatus.EXPIRED: set(),
    ApplicationStatus.ON_HOLD: {
        ApplicationStatus.SAVED,
        ApplicationStatus.READY_TO_APPLY,
        ApplicationStatus.APPLIED,
        ApplicationStatus.APPLICATION_VIEWED,
        ApplicationStatus.SCREENING,
        ApplicationStatus.INTERVIEW,
        ApplicationStatus.TECHNICAL_INTERVIEW,
        ApplicationStatus.FINAL_INTERVIEW,
        ApplicationStatus.OFFER,
        ApplicationStatus.WITHDRAWN,
    },
}

# States that require a reason when transitioning away
_REASON_REQUIRED_FROM: Set[ApplicationStatus] = {
    ApplicationStatus.REJECTED,
    ApplicationStatus.WITHDRAWN,
    ApplicationStatus.EXPIRED,
    ApplicationStatus.ACCEPTED,
    ApplicationStatus.OFFER,
}

# Terminal states (no outgoing transitions)
_TERMINAL_STATES: Set[ApplicationStatus] = {
    ApplicationStatus.ACCEPTED,
    ApplicationStatus.REJECTED,
    ApplicationStatus.WITHDRAWN,
    ApplicationStatus.EXPIRED,
}


@dataclass(frozen=True)
class TransitionResult:
    """Result of a state transition validation."""

    allowed: bool
    from_status: ApplicationStatus
    to_status: ApplicationStatus
    reason_required: bool = False
    message: Optional[str] = None


@dataclass(frozen=True)
class StateMachineInfo:
    """State machine metadata for an application."""

    current_status: ApplicationStatus
    allowed_transitions: List[TransitionResult]
    is_terminal: bool
    can_reopen: bool = False


class ApplicationStateMachine:
    """Application lifecycle state machine.

    Enforces legal transitions, records required metadata, and provides
    machine-readable transition validation for the API layer.
    """

    @classmethod
    def get_allowed_transitions(cls, current_status: ApplicationStatus) -> List[TransitionResult]:
        """Return all allowed transitions from the given status."""
        allowed = _ALLOWED_TRANSITIONS.get(current_status, set())
        results = []
        for to_status in allowed:
            results.append(TransitionResult(
                allowed=True,
                from_status=current_status,
                to_status=to_status,
                reason_required=(current_status in _REASON_REQUIRED_FROM),
            ))
        return results

    @classmethod
    def can_transition(cls, from_status: ApplicationStatus, to_status: ApplicationStatus) -> TransitionResult:
        """Check if a specific transition is legal."""
        allowed = _ALLOWED_TRANSITIONS.get(from_status, set())
        if to_status not in allowed:
            return TransitionResult(
                allowed=False,
                from_status=from_status,
                to_status=to_status,
                message=f"Transition from {from_status.value} to {to_status.value} is not allowed",
            )
        return TransitionResult(
            allowed=True,
            from_status=from_status,
            to_status=to_status,
            reason_required=(from_status in _REASON_REQUIRED_FROM),
        )

    @classmethod
    def is_terminal(cls, status: ApplicationStatus) -> bool:
        """Return True if the status is terminal (no outgoing transitions)."""
        return status in _TERMINAL_STATES

    @classmethod
    def get_state_machine_info(cls, current_status: ApplicationStatus) -> StateMachineInfo:
        """Return full state machine info for the given status."""
        allowed = cls.get_allowed_transitions(current_status)
        return StateMachineInfo(
            current_status=current_status,
            allowed_transitions=allowed,
            is_terminal=cls.is_terminal(current_status),
            can_reopen=(current_status in _TERMINAL_STATES and current_status != ApplicationStatus.ACCEPTED),
        )

    @classmethod
    def record_transition(
        cls,
        application,
        to_status: ApplicationStatus,
        reason: Optional[str] = None,
        actor_type: str = "manual",
        actor_id: Optional[str] = None,
    ) -> tuple[bool, Optional[str]]:
        """Record a state transition on an application object.

        Mutates the application in place:
        - Sets previous_status to current status
        - Sets status to to_status
        - Sets closed_at if transitioning to a terminal state
        - Sets applied_at if transitioning to APPLIED for the first time

        Args:
            application: SQLAlchemy Application model instance
            to_status: Target status
            reason: Optional reason for the transition
            actor_type: Who performed the transition
            actor_id: ID of the actor

        Returns:
            (success: bool, error_message: Optional[str])
        """
        from_status = application.status
        result = cls.can_transition(from_status, to_status)
        if not result.allowed:
            return False, result.message
        if result.reason_required and not reason:
            return False, f"A reason is required when transitioning from {from_status.value}"
        now = datetime.now(timezone.utc)
        application.previous_status = from_status.value
        application.status = to_status
        if cls.is_terminal(to_status):
            application.closed_at = now
        if to_status == ApplicationStatus.APPLIED and application.applied_at is None:
            application.applied_at = now
        if to_status != ApplicationStatus.ON_HOLD:
            application.last_activity_at = now
        return True, None
