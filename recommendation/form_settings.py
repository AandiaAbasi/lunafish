"""Translation field visibility for the placement-test management screens.

Both languages are part of the actual exam content, so hiding one language is
no longer supported, regardless of older deployment environment flags.
"""


def show_translation_fields():
    """Always display editable Persian and English fields in the test builder."""
    return True
