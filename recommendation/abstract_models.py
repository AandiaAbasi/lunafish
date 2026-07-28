from django.db import models
from django.utils import timezone
from django.utils.translation import get_language, gettext_lazy as _
import jdatetime


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True, verbose_name=_("Created at"))
    updated_at = models.DateTimeField(auto_now=True, null=True, verbose_name=_("Updated at"))

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def _format_datetime(self, dt):
        if not dt:
            return "-"

        try:
            dt = timezone.localtime(dt)
        except Exception:
            pass

        lang = (get_language() or '').lower()

        if lang.startswith("fa"):
            return jdatetime.datetime.fromgregorian(
                datetime=dt
            ).strftime('%Y/%m/%d %H:%M:%S')
        elif lang.startswith("ar"):
            from hijridate import Gregorian
            hijri = Gregorian(dt.year, dt.month, dt.day).to_hijri()
            return f"{hijri.year}/{hijri.month:02d}/{hijri.day:02d} {dt.strftime('%H:%M:%S')}"
        else:
            return dt.strftime('%Y-%m-%d %H:%M:%S')

    def created_at_display(self):
        return self._format_datetime(self.created_at)
    created_at_display.short_description = _("Created at")

    def updated_at_display(self):
        return self._format_datetime(self.updated_at)
    updated_at_display.short_description = _("Updated at")
