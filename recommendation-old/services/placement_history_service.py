from __future__ import annotations

from typing import Any

import jdatetime
from django.utils import timezone

from recommendation.models import EnglishPlacementAssessment, TestScale


def numeric_score(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def format_datetime_payload(value):
    if not value:
        return {
            "iso": None,
            "jalali": "",
        }

    try:
        local_value = timezone.localtime(value)
    except Exception:
        local_value = value

    return {
        "iso": value.isoformat(),
        "jalali": jdatetime.datetime.fromgregorian(
            datetime=local_value
        ).strftime("%Y/%m/%d - %H:%M"),
    }


def serialize_student(student):
    selected_avatar = getattr(student, "selected_avatar", None)
    avatar_url = None

    if selected_avatar:
        avatar_image = getattr(selected_avatar, "image", None)

        if avatar_image:
            try:
                avatar_url = avatar_image.url
            except (ValueError, AttributeError):
                avatar_url = None

    return {
        "id": student.id,
        "name": getattr(student, "name", "") or "",
        "username": getattr(student, "username", "") or "",
        "email": getattr(student, "email", "") or "",
        "phone": str(getattr(student, "phone", "") or ""),

        "profile_photo": avatar_url,

        "selected_avatar": (
            {
                "id": selected_avatar.id,
                "image": avatar_url,
            }
            if selected_avatar
            else None
        ),

        "current_english_level": getattr(
            student,
            "english_level",
            None,
        ),
        "english_level_source": getattr(
            student,
            "english_level_source",
            None,
        ),
        "english_level_updated_at": format_datetime_payload(
            getattr(student, "english_level_updated_at", None)
        ),
    }


def normalize_level_value(value) -> str:
    if value is None:
        return ""
    return str(value).strip().lower().replace("-", "_")


def serialize_online_class(assessment):
    """
    Serialize the online class created from one placement assessment.

    The payload intentionally contains both presentation fields and everything
    the student list needs to decide whether the existing join endpoint can be
    called. The actual room join data is still returned by POST /classes/{id}/join/.
    """
    try:
        online_class = assessment.online_class
    except Exception:
        online_class = None

    if not online_class:
        return None

    teacher = online_class.teacher
    status_value = online_class.status
    actual_start = online_class.actual_start
    actual_end = online_class.actual_end

    can_join = bool(
        status_value == online_class.STATUS_ACTIVE
        and actual_start
        and not actual_end
    )

    if can_join:
        join_state = "joinable"
        join_message = "کلاس فعال است و امکان پیوستن وجود دارد."
    elif status_value == online_class.STATUS_SCHEDULED:
        join_state = "not_started"
        join_message = "کلاس هنوز توسط معلم شروع نشده است."
    elif status_value == online_class.STATUS_ENDED or actual_end:
        join_state = "ended"
        join_message = "کلاس پایان یافته است."
    elif status_value == online_class.STATUS_CANCELLED:
        join_state = "cancelled"
        join_message = "کلاس لغو شده است."
    else:
        join_state = "unavailable"
        join_message = "در حال حاضر امکان پیوستن به کلاس وجود ندارد."

    enrolled_count = getattr(
        assessment,
        "online_class_enrolled_count",
        None,
    )
    if enrolled_count is None:
        try:
            enrolled_count = online_class.enrolled_count
        except Exception:
            enrolled_count = 0

    source_type = getattr(online_class, "source_type", None)
    if not source_type:
        source_type = (
            "placement_assessment"
            if getattr(online_class, "placement_assessment_id", None)
            else "booking"
        )

    return {
        "id": str(online_class.id),
        "title": online_class.title,
        "description": online_class.description,
        "status": status_value,
        "status_display": online_class.get_status_display(),
        "class_source": source_type,
        "placement_assessment_id": assessment.id,
        "scheduled_start": format_datetime_payload(online_class.scheduled_start),
        "scheduled_end": format_datetime_payload(online_class.scheduled_end),
        "actual_start": format_datetime_payload(actual_start),
        "actual_end": format_datetime_payload(actual_end),
        "room_id": str(online_class.room_id),
        "max_students": online_class.max_students,
        "enrolled_count": int(enrolled_count or 0),
        "is_full": int(enrolled_count or 0) >= online_class.max_students,
        "teacher": {
            "id": teacher.id,
            "name": getattr(teacher, "name", "") or "",
            "username": getattr(teacher, "username", "") or "",
        },
        "settings": {
            "allow_student_chat": online_class.allow_student_chat,
            "allow_student_reactions": online_class.allow_student_reactions,
            "require_approval_to_join": online_class.require_approval_to_join,
            "enable_recording": online_class.enable_recording,
        },
        "can_join": can_join,
        "join_state": join_state,
        "join_message": join_message,
    }


def _assessment_test(assessment):
    if assessment.test_id:
        return assessment.test
    if assessment.response_id and assessment.response:
        return assessment.response.test
    return None


def _serialize_interpretation(scale, score):
    for item in scale.interpretations.all():
        if item.min_score <= score <= item.max_score:
            return {
                "id": item.id,
                "title": item.title,
                "level": item.title,
                "description": item.description,
                "min_score": numeric_score(item.min_score),
                "max_score": numeric_score(item.max_score),
                "order": item.order,
            }
    return None


def _serialize_level(value, level_scale_map, fallback_label=""):
    normalized = normalize_level_value(value)
    if not normalized:
        return None

    configured = level_scale_map.get(normalized)
    if configured:
        return {
            "id": configured["id"],
            "code": configured["code"],
            "title": configured["title"],
            "description": configured["description"],
            "rank": configured["rank"],
        }

    return {
        "id": None,
        "code": str(value).replace("_", "-").upper(),
        "title": fallback_label,
        "description": "",
        "rank": None,
    }


def build_assessment_details(assessment: EnglishPlacementAssessment):
    """
    Serialize one immutable placement history item from its score/summary snapshots.

    Scale metadata and interpretation text come from the current test configuration,
    while numeric scores and the suggested result come from the assessment snapshot.
    """
    test = _assessment_test(assessment)
    raw_scores = assessment.raw_scores_snapshot or {}
    summary = assessment.result_summary_snapshot or {}

    scales = []
    if test:
        scales = list(
            TestScale.objects
            .filter(test=test)
            .prefetch_related("interpretations")
        )

    scale_details_map = {
        str(item.get("code")): item
        for item in summary.get("scale_details", [])
        if isinstance(item, dict) and item.get("code") is not None
    }

    scale_results = []
    for scale in scales:
        raw_score = numeric_score(raw_scores.get(scale.code, 0))
        detail = scale_details_map.get(str(scale.code), {})
        percentage = numeric_score(detail.get("percentage", raw_score))
        percentage = max(0.0, min(100.0, percentage))
        pass_score = numeric_score(scale.pass_score)

        item = {
            "id": scale.id,
            "code": scale.code,
            "name": scale.title,
            "title": scale.title,
            "description": scale.description,
            "scale_type": scale.scale_type,
            "rank": scale.rank,
            "raw_score": round(raw_score, 6),
            "percentage": round(percentage, 2),
            "pass_score": pass_score,
            "interpretation": _serialize_interpretation(scale, raw_score),
        }

        if scale.scale_type == TestScale.ScaleType.LEVEL:
            item["passed"] = raw_score >= pass_score

        scale_results.append(item)

    level_results = sorted(
        [
            item for item in scale_results
            if item["scale_type"] == TestScale.ScaleType.LEVEL
        ],
        key=lambda item: (
            item["rank"] is None,
            item["rank"] if item["rank"] is not None else 0,
            item["id"],
        ),
    )

    skill_results = sorted(
        [
            item for item in scale_results
            if item["scale_type"] == TestScale.ScaleType.SKILL
        ],
        key=lambda item: (
            item["rank"] is None,
            item["rank"] if item["rank"] is not None else 0,
            item["id"],
        ),
    )

    other_results = [
        item for item in scale_results
        if item["scale_type"] not in {
            TestScale.ScaleType.LEVEL,
            TestScale.ScaleType.SKILL,
        }
    ]

    level_scale_map = {
        normalize_level_value(item["code"]): item
        for item in level_results
    }

    suggested_value = assessment.suggested_level or summary.get("suggested_level")
    final_value = assessment.final_level

    suggested_level = _serialize_level(
        suggested_value,
        level_scale_map,
        assessment.get_suggested_level_display() if assessment.suggested_level else "",
    )
    final_level = _serialize_level(
        final_value,
        level_scale_map,
        assessment.get_final_level_display() if assessment.final_level else "",
    )
    display_level = final_level or suggested_level

    created_at = format_datetime_payload(assessment.created_at)
    assessed_at = format_datetime_payload(assessment.assessed_at)
    response_completed_at = format_datetime_payload(
        assessment.response_completed_at
    )

    test_data = None
    if test:
        test_data = {
            "id": test.id,
            "title": test.title,
            "description": test.description,
            "test_type": test.test_type,
        }

    assessed_by = None
    if assessment.assessed_by_id:
        assessed_by = {
            "id": assessment.assessed_by_id,
            "name": getattr(assessment.assessed_by, "name", "") or "",
            "username": getattr(assessment.assessed_by, "username", "") or "",
            "role": getattr(assessment.assessed_by, "role", None),
        }

    placement = {
        "suggested_level": suggested_level,
        "final_level": final_level,
        "display_level": display_level,
        "is_final": bool(final_level),
        "status": assessment.status,
        "status_display": assessment.get_status_display(),
        "source": assessment.source,
        "source_display": assessment.get_source_display(),
        "assessed_by": assessed_by,
        "assessed_at": assessed_at,
        "note": assessment.note,
    }

    return {
        "assessment": {
            "id": assessment.id,
            "created_at": created_at,
            "response_completed_at": response_completed_at,
            "response_id": assessment.response_id,
        },
        "test": test_data,
        "placement": placement,
        "result": {
            "result_type": summary.get("result_type", "english_placement"),
            "raw_scores": raw_scores,
            "summary": summary,
        },
        "level_results": level_results,
        "skill_results": skill_results,
        "other_results": other_results,
        "scale_results": scale_results,
        "online_class": serialize_online_class(assessment),
        "can_create_online_class": not bool(getattr(assessment, "online_class", None)),
        "historical_answers_available": False,
    }


def build_assessment_list_item(assessment: EnglishPlacementAssessment):
    details = build_assessment_details(assessment)

    return {
        "id": assessment.id,
        "test": details["test"],
        "placement": details["placement"],
        "created_at": details["assessment"]["created_at"],
        "response_completed_at": details["assessment"]["response_completed_at"],
        "response_id": assessment.response_id,
        "online_class": details["online_class"],
        "can_create_online_class": details["can_create_online_class"],
        "level_results": details["level_results"],
        "skill_results": details["skill_results"],
    }
