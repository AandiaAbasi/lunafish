from django.db import models
from django.utils import timezone
from django.utils.translation import get_language, gettext_lazy as _
import jdatetime


class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, null=True,verbose_name=_("Created at"))
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

        lang = get_language()  

        if lang and lang.startswith("fa"):
            return jdatetime.datetime.fromgregorian(
                datetime=dt
            ).strftime('%H:%M:%S %Y-%m-%d')
        else:
            return dt.strftime('%H:%M:%S %Y-%m-%d')

    def created_at_display(self):
        return self._format_datetime(self.created_at)
    created_at_display.short_description = _("Created at")

    def updated_at_display(self):
        return self._format_datetime(self.updated_at)
    updated_at_display.short_description = _("Updated at")
