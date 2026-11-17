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
    """Use the selected translation; fall back only for older untranslated rows."""
    preferred = getattr(instance, f"{field_name}_{language}", None)
    if preferred is not None and str(preferred).strip():
        return preferred
    fallback = "fa" if language == "en" else "en"
    return getattr(instance, f"{field_name}_{fallback}", "") or ""


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
