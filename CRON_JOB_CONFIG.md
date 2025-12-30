"""
Django Cron Jobs Configuration

این فایل نمونه‌ای برای configure کردن cron job‌های scheduled است.
شما می‌توانید از چند روش استفاده کنید:

1. APScheduler (توصیه‌شده برای Django)
2. Celery + Beat
3. System Cron
"""

# ============ Option 1: APScheduler (Recommended) ============
# pip install apscheduler

APSCHEDULER_DATETIME_FORMAT = "N j, Y, f:s a"

SCHEDULER_CONFIG = {
    "default": {
        "type": "background",
        "apscheduler.executors.default": {
            "class": "apscheduler.executors.base:BaseExecutor"
        },
        "apscheduler.job_stores.default": {
            "class": "apscheduler.jobstores.memory:MemoryJobStore"
        },
        "apscheduler.timezone": "Asia/Tehran",
    }
}

# ============ Option 2: Django-Crontab ============
# pip install django-crontab

CRONJOBS = [
    # Run every hour
    ('0 * * * *', 'classroom.management.commands.expire_availability_slots', ['--quiet']),
    
    # Run every 30 minutes
    ('*/30 * * * *', 'classroom.management.commands.expire_availability_slots'),
    
    # Run daily at 00:00
    ('0 0 * * *', 'classroom.management.commands.expire_availability_slots'),
]

# ============ Option 3: System Cron (Linux/Mac) ============
# Add to crontab -e:
# 0 * * * * /path/to/venv/bin/python /path/to/manage.py expire_availability_slots
# */30 * * * * /path/to/venv/bin/python /path/to/manage.py expire_availability_slots

# ============ Option 4: Celery Beat ============
# from celery.schedules import crontab
# 
# CELERY_BEAT_SCHEDULE = {
#     'expire-availability-slots-every-hour': {
#         'task': 'classroom.tasks.expire_availability_slots',
#         'schedule': crontab(minute=0),  # Every hour
#     },
# }
