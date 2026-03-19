from enum import Enum


class PermissionStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    ISSUED = "issued"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class LeaseStatus(str, Enum):
    DRAFT = "draft"
    NEGOTIATING = "negotiating"
    PENDING_APPROVAL = "pending_approval"
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"


# 設計書 §2.4.2, §2.4.4 に基づく遷移ルール
PERMISSION_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["submitted"],
    "submitted": ["under_review"],
    "under_review": ["rejected", "pending_approval"],
    "pending_approval": ["rejected", "approved"],
    "approved": ["issued", "expired", "cancelled"],
    "issued": ["expired", "cancelled"],
    "rejected": ["submitted"],
    # expired, cancelled は終端状態（更新は新レコードで表現）
}

LEASE_TRANSITIONS: dict[str, list[str]] = {
    "draft": ["negotiating"],
    "negotiating": ["pending_approval"],
    "pending_approval": ["negotiating", "active"],
    "active": ["expired", "terminated"],
    # expired, terminated は終端状態（更新は新レコードで表現）
}


def is_valid_transition(case_type: str, current_status: str, new_status: str) -> bool:
    """ステータス遷移が許可されているか検証する。"""
    transitions = (
        PERMISSION_TRANSITIONS if case_type == "permission"
        else LEASE_TRANSITIONS if case_type == "lease"
        else {}
    )
    allowed = transitions.get(current_status, [])
    return new_status in allowed


def get_allowed_transitions(case_type: str, current_status: str) -> list[str]:
    """現在のステータスから遷移可能なステータス一覧を取得する。"""
    transitions = (
        PERMISSION_TRANSITIONS if case_type == "permission"
        else LEASE_TRANSITIONS if case_type == "lease"
        else {}
    )
    return transitions.get(current_status, [])
