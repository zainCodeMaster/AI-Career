"""Phase 7 CRM state machine tests."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.db.models.crm import Application, ApplicationStatus
from app.db.models.user import User
from app.services.crm.state_machine import ApplicationStateMachine, TransitionResult
from app.core.security import get_password_hash


@pytest.fixture
def test_user_obj(db_session):
    user = User(
        email="crm_sm@example.com",
        full_name="State Machine User",
        password_hash=get_password_hash("StrongPass123"),
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


class TestStateMachineTransitions:
    def test_initial_status(self, test_user_obj):
        result = ApplicationStateMachine.get_state_machine_info(ApplicationStatus.SAVED)
        assert result.current_status == ApplicationStatus.SAVED
        assert not result.is_terminal

    def test_saved_to_applied(self, test_user_obj):
        result = ApplicationStateMachine.can_transition(ApplicationStatus.SAVED, ApplicationStatus.APPLIED)
        assert result.allowed

    def test_saved_to_rejected_not_allowed(self, test_user_obj):
        result = ApplicationStateMachine.can_transition(ApplicationStatus.SAVED, ApplicationStatus.REJECTED)
        assert not result.allowed

    def test_applied_to_rejected_allowed(self, test_user_obj):
        result = ApplicationStateMachine.can_transition(ApplicationStatus.APPLIED, ApplicationStatus.REJECTED)
        assert result.allowed

    def test_terminal_states(self, test_user_obj):
        for status in [ApplicationStatus.ACCEPTED, ApplicationStatus.REJECTED, ApplicationStatus.WITHDRAWN, ApplicationStatus.EXPIRED]:
            result = ApplicationStateMachine.get_state_machine_info(status)
            assert result.is_terminal
            assert len(result.allowed_transitions) == 0

    def test_on_hold_resume(self, test_user_obj):
        result = ApplicationStateMachine.can_transition(ApplicationStatus.ON_HOLD, ApplicationStatus.APPLIED)
        assert result.allowed

    def test_reopen_from_rejected_requires_reason(self, test_user_obj):
        from app.services.crm.state_machine import _REASON_REQUIRED_FROM
        assert ApplicationStatus.REJECTED in _REASON_REQUIRED_FROM

    def test_record_transition_success(self, db_session, test_user_obj):
        app = Application(user_id=test_user_obj.id, status=ApplicationStatus.SAVED)
        db_session.add(app)
        db_session.commit()
        success, error = ApplicationStateMachine.record_transition(
            application=app,
            to_status=ApplicationStatus.APPLIED,
            reason="Submitting now",
            actor_type="manual",
            actor_id=str(test_user_obj.id),
        )
        assert success
        assert error is None
        assert app.status == ApplicationStatus.APPLIED
        assert app.previous_status == ApplicationStatus.SAVED.value
        assert app.applied_at is not None

    def test_record_transition_failure(self, db_session, test_user_obj):
        app = Application(user_id=test_user_obj.id, status=ApplicationStatus.SAVED)
        db_session.add(app)
        db_session.commit()
        success, error = ApplicationStateMachine.record_transition(
            application=app,
            to_status=ApplicationStatus.REJECTED,
        )
        assert not success
        assert error is not None

    def test_record_transition_requires_reason(self, db_session, test_user_obj):
        app = Application(user_id=test_user_obj.id, status=ApplicationStatus.OFFER)
        db_session.add(app)
        db_session.commit()
        success, error = ApplicationStateMachine.record_transition(
            application=app,
            to_status=ApplicationStatus.REJECTED,
        )
        assert not success
        assert "reason" in error.lower()
