"""Utility serializers for feedback endpoints."""

from __future__ import annotations

from typing import Any, Dict

from sqlalchemy.exc import MissingGreenlet

from models.feedback import Feedback


def _safe_coach_name(feedback: Feedback) -> str | None:
    """Return coach name without triggering lazy loads in async context."""
    try:
        coach = feedback.coach
    except MissingGreenlet:
        return None
    return coach.full_name if coach else None


def serialize_feedback(feedback: Feedback) -> Dict[str, Any]:
    """Convert a Feedback ORM instance into a serializable dictionary."""
    return {
        "id": feedback.id,
        "media_id": feedback.media_id,
        "coach_user_id": feedback.coach_user_id,
        "parent_feedback_id": feedback.parent_feedback_id,
        "content": feedback.content,
        "annotation_data": feedback.annotation_data,
        "created_at": feedback.created_at,
        "updated_at": feedback.updated_at,
        "coach_name": _safe_coach_name(feedback),
        "replies": [],
    }

