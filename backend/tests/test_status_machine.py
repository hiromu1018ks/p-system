import pytest
from services.status_machine import is_valid_transition, get_allowed_transitions


class TestPermissionTransitions:
    def test_draft_to_submitted(self):
        assert is_valid_transition("permission", "draft", "submitted") is True

    def test_submitted_to_under_review(self):
        assert is_valid_transition("permission", "submitted", "under_review") is True

    def test_under_review_to_pending_approval(self):
        assert is_valid_transition("permission", "under_review", "pending_approval") is True

    def test_pending_approval_to_approved(self):
        assert is_valid_transition("permission", "pending_approval", "approved") is True

    def test_approved_to_issued(self):
        assert is_valid_transition("permission", "approved", "issued") is True

    def test_approved_to_expired(self):
        assert is_valid_transition("permission", "approved", "expired") is True

    def test_approved_to_cancelled(self):
        assert is_valid_transition("permission", "approved", "cancelled") is True

    def test_under_review_to_rejected(self):
        assert is_valid_transition("permission", "under_review", "rejected") is True

    def test_pending_approval_to_rejected(self):
        assert is_valid_transition("permission", "pending_approval", "rejected") is True

    def test_rejected_to_submitted(self):
        """差戻し後の再申請"""
        assert is_valid_transition("permission", "rejected", "submitted") is True

    def test_invalid_draft_to_approved(self):
        assert is_valid_transition("permission", "draft", "approved") is False

    def test_invalid_approved_to_submitted(self):
        """逆戻り禁止"""
        assert is_valid_transition("permission", "approved", "submitted") is False

    def test_invalid_expired_to_approved(self):
        """expired は終端状態"""
        assert is_valid_transition("permission", "expired", "approved") is False

    def test_invalid_cancelled_to_draft(self):
        """cancelled は終端状態"""
        assert is_valid_transition("permission", "cancelled", "draft") is False


class TestLeaseTransitions:
    def test_draft_to_negotiating(self):
        assert is_valid_transition("lease", "draft", "negotiating") is True

    def test_negotiating_to_pending_approval(self):
        assert is_valid_transition("lease", "negotiating", "pending_approval") is True

    def test_pending_approval_to_active(self):
        assert is_valid_transition("lease", "pending_approval", "active") is True

    def test_pending_approval_to_negotiating(self):
        """差戻し"""
        assert is_valid_transition("lease", "pending_approval", "negotiating") is True

    def test_active_to_expired(self):
        assert is_valid_transition("lease", "active", "expired") is True

    def test_active_to_terminated(self):
        assert is_valid_transition("lease", "active", "terminated") is True

    def test_invalid_draft_to_active(self):
        assert is_valid_transition("lease", "draft", "active") is False

    def test_invalid_active_to_draft(self):
        assert is_valid_transition("lease", "active", "draft") is False

    def test_invalid_terminated_to_active(self):
        """terminated は終端状態"""
        assert is_valid_transition("lease", "terminated", "active") is False


class TestGetAllowedTransitions:
    def test_permission_draft_allowed(self):
        allowed = get_allowed_transitions("permission", "draft")
        assert "submitted" in allowed
        assert "approved" not in allowed

    def test_permission_approved_allowed(self):
        allowed = get_allowed_transitions("permission", "approved")
        assert "issued" in allowed
        assert "expired" in allowed
        assert "cancelled" in allowed
        assert "submitted" not in allowed

    def test_lease_active_allowed(self):
        allowed = get_allowed_transitions("lease", "active")
        assert "expired" in allowed
        assert "terminated" in allowed
        assert "draft" not in allowed

    def test_unknown_status(self):
        allowed = get_allowed_transitions("permission", "unknown_status")
        assert allowed == []

    def test_unknown_case_type(self):
        allowed = get_allowed_transitions("unknown_type", "draft")
        assert allowed == []
