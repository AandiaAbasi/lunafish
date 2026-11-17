"""Locale-safe access to modeltranslation fields for placement tests.

The student app supplies Accept-Language: en or fa. Resolve the language
from each request rather than relying on Django's current global language.
"""
from django.utils.translation import get_language_from_request


def test_language(request):
    explicit = (request.query_params.get("lang") if hasattr(request, "query_params")
                else request.GET.get("lang", ""))
    explicit = str(explicit or "").lower().split("-", 1)[0]
    if explicit in ("en", "fa"):
        return explicit
    detected = get_language_from_request(request)
    return "en" if (detected or "").lower().split("-", 1)[0] == "en" else "fa"


def localized_text(instance, field_name, language):
    """Return only the requested language; never show Persian in English mode."""
    value = getattr(instance, f"{field_name}_{language}", None)
    return str(value) if value is not None else ""


STATUS_LABELS = {
    "not_started": ("Not started", "شروع نشده"),
    "in_progress": ("In progress", "در حال پاسخ"),
    "completed": ("Completed", "تکمیل شده"),
}
QUESTION_TYPE_LABELS = {
    "multiple_choice": ("Multiple choice", "چند گزینه‌ای"),
    "text_input": ("Short text", "ورودی متنی کوتاه"),
    "textarea": ("Long text", "متن بلند"),
}


def localized_label(code, labels, language):
    values = labels.get(code)
    return values[0 if language == "en" else 1] if values else str(code or "")
