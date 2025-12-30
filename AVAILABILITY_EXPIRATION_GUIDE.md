# Availability Slots Expiration System

## Overview

سیستم خودکار برای منقضی کردن (expire کردن) بازه‌های زمانی معلمان که از تاریخ/زمان گذشته باشند.

## Features

✅ **Automatic Expiration** - خودکار منقضی شدن بازه‌های گذشته
✅ **Cron Job Support** - اجرای scheduled برای بررسی منقضی‌شدن
✅ **API Status** - نمایش وضعیت expiration در API
✅ **Admin Display** - نمایش در Django admin
✅ **Soft Status** - صرفاً علامت‌گذاری، حذف نمی‌شود

---

## Database Schema

### New Field in TeacherAvailability

```python
is_expired = models.BooleanField(
    default=False,
    verbose_name="منقضی شده",
    help_text="آیا این بازه زمانی منقضی شده است؟"
)
```

### Migration

```bash
python manage.py migrate classroom
```

---

## Management Command

### Run Manual Expiration Check

```bash
# Check and expire old slots
python manage.py expire_availability_slots

# Dry-run mode (show what would be expired without changing)
python manage.py expire_availability_slots --dry-run

# Silent mode (no output)
python manage.py expire_availability_slots --quiet
```

---

## Cron Job Setup

### Option 1: Django-Crontab (Simple)

**Install:**
```bash
pip install django-crontab
```

**Add to settings.py:**
```python
INSTALLED_APPS = [
    ...
    'django_crontab',
]

CRONJOBS = [
    # Run every hour at :00
    ('0 * * * *', 'classroom.management.commands.expire_availability_slots'),
    
    # OR run every 30 minutes
    ('*/30 * * * *', 'classroom.management.commands.expire_availability_slots'),
    
    # OR run daily at midnight
    ('0 0 * * *', 'classroom.management.commands.expire_availability_slots'),
]
```

**Install cron schedule:**
```bash
python manage.py crontab add
```

**View installed crons:**
```bash
python manage.py crontab show
```

**Remove crons:**
```bash
python manage.py crontab remove
```

---

### Option 2: Linux/Mac Cron (System Level)

**Edit crontab:**
```bash
crontab -e
```

**Add this line (run every hour):**
```bash
0 * * * * /path/to/venv/bin/python /path/to/manage.py expire_availability_slots
```

**Run every 30 minutes:**
```bash
*/30 * * * * /path/to/venv/bin/python /path/to/manage.py expire_availability_slots
```

---

### Option 3: Celery Beat (For Distributed Systems)

**Create task in tasks.py:**
```python
from celery import shared_task
from django.core.management import call_command

@shared_task
def expire_availability_slots():
    call_command('expire_availability_slots')
```

**Add to celery beat schedule in settings.py:**
```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'expire-slots-hourly': {
        'task': 'classroom.tasks.expire_availability_slots',
        'schedule': crontab(minute=0),  # Every hour
    },
}
```

**Run celery beat:**
```bash
celery -A fofofish beat -l info
```

---

## API Response

### API Response with is_expired

```json
GET /api/teacher/availability/

{
  "results": [
    {
      "id": 123,
      "teacher": 1,
      "teacher_name": "علی محمدی",
      "date": "1404/10/08",
      "start_time": "10:00",
      "end_time": "11:00",
      "price": "300000",
      "discount_price": null,
      "is_available": false,
      "is_booked": false,
      "is_expired": true,  // ← Expired!
      "notes": null,
      "created_at": "2025-01-01T10:00:00Z",
      "updated_at": "2025-01-02T14:30:00Z"
    },
    {
      "id": 124,
      "teacher": 1,
      "teacher_name": "علی محمدی",
      "date": "2025-04-15",
      "start_time": "14:00",
      "end_time": "15:00",
      "price": "300000",
      "discount_price": null,
      "is_available": true,
      "is_booked": false,
      "is_expired": false,  // ← Active!
      "notes": null,
      "created_at": "2025-01-02T10:00:00Z",
      "updated_at": "2025-01-02T15:00:00Z"
    }
  ]
}
```

---

## Admin Interface

في Django Admin:
- ✅ بازه‌های expired نمایش داده می‌شوند
- ✅ Status column نشان‌دهنده "منقضی شده" یا "فعال"
- ✅ Filter برای دیدن فقط expired یا active slots

---

## Model Methods

### check_and_expire()

بررسی و منقضی کردن اگر زمان گذشته باشد:

```python
slot = TeacherAvailability.objects.get(id=123)
if slot.check_and_expire():
    print("Slot was expired")
else:
    print("Slot is still valid")
```

### is_past()

بررسی اینکه آیا زمان گذشته است:

```python
if slot.is_past():
    print("This slot is in the past")
```

---

## Monitoring & Logging

### Add Logging to Command

```python
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    def handle(self, *args, **options):
        logger.info(f'Expiring slots at {datetime.now()}')
        # ... rest of command
        logger.info(f'Expired {expired_count} slots')
```

### View Logs

```bash
# If using django-crontab, view logs:
tail -f /var/log/django-crontab.log
```

---

## Testing

### Manual Test

```python
from classroom.models import TeacherAvailability
from datetime import datetime, timedelta

# Get a past slot
slot = TeacherAvailability.objects.first()

# Manually set date to past
slot.date = (datetime.now() - timedelta(days=1)).date()
slot.save()

# Run expiration
slot.check_and_expire()

# Check if expired
print(slot.is_expired)  # True
```

### Test with Command

```bash
python manage.py expire_availability_slots --dry-run
```

---

## Scheduling Examples

| Frequency | Cron Expression | Description |
|-----------|-----------------|-------------|
| Every hour | `0 * * * *` | At minute 0 of every hour |
| Every 30 mins | `*/30 * * * *` | Every 30 minutes |
| Every 15 mins | `*/15 * * * *` | Every 15 minutes |
| Daily at midnight | `0 0 * * *` | 00:00 every day |
| Daily at 6 AM | `0 6 * * *` | 06:00 every day |
| Weekly (Sunday) | `0 0 * * 0` | Sunday at 00:00 |

---

## Troubleshooting

### Cron not running?

```bash
# Check if cron service is running
sudo service cron status

# Check system crontab
crontab -l

# View cron logs
grep CRON /var/log/syslog
```

### Permission issues?

```bash
# Make sure manage.py is executable
chmod +x manage.py

# Run with full path to python
/usr/bin/python3 /full/path/to/manage.py expire_availability_slots
```

### Slots not expiring?

```python
# Check if slots exist
TeacherAvailability.objects.count()

# Check if any are past date
from datetime import datetime
TeacherAvailability.objects.filter(date__lt=datetime.now().date()).count()

# Manually run expiration
from django.core.management import call_command
call_command('expire_availability_slots')
```

---

## Performance

- ✅ Indexed on `is_expired` for fast queries
- ✅ Bulk operations for large datasets
- ✅ Only checks non-expired slots (optimized)
- ✅ No heavy computations

---

## Future Enhancements

- [ ] Automatic email notification to teacher when slot expires
- [ ] Telegram/SMS notification
- [ ] Refund to students if booking was expired
- [ ] Archive old expired slots to separate table
