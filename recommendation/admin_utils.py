import jdatetime

from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def format_jalali_datetime(value, include_seconds=False):
    """Return a timezone-aware datetime in Jalali format for admin screens."""
    if not value:
        return _("ثبت نشده")

    try:
        value = timezone.localtime(value)
    except (ValueError, TypeError):
        pass

    date_format = "%Y/%m/%d - %H:%M:%S" if include_seconds else "%Y/%m/%d - %H:%M"
    return jdatetime.datetime.fromgregorian(datetime=value).strftime(date_format)
