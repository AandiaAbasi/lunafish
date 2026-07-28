import os

from django.conf import settings


TRUE_VALUES = {"1", "true", "yes", "on"}


def show_translation_fields():
    """Return whether secondary-language fields should be visible in recommendation forms."""
    value = getattr(
        settings,
        "RECOMMENDATION_SHOW_TRANSLATION_FIELDS",
        os.getenv("RECOMMENDATION_SHOW_TRANSLATION_FIELDS", "false"),
    )

    if isinstance(value, bool):
        return value

    return str(value).strip().lower() in TRUE_VALUES
