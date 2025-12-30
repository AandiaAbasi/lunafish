"""
Cron job command to mark expired availability slots
This command should be run periodically (e.g., every hour)
"""
from django.core.management.base import BaseCommand
from django.utils.translation import gettext_lazy as _
from classroom.models import TeacherAvailability
from datetime import datetime


class Command(BaseCommand):
    help = 'Mark expired teacher availability slots'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually expiring slots',
        )

    def handle(self, *args, **options):
        dry_run = options.get('dry_run', False)
        
        # Get all non-expired slots
        slots = TeacherAvailability.objects.filter(is_expired=False)
        
        expired_count = 0
        current_time = datetime.now()
        
        self.stdout.write(
            self.style.SUCCESS(f'🔍 Checking {slots.count()} active slots...')
        )
        
        for slot in slots:
            if slot.check_and_expire():
                expired_count += 1
                self.stdout.write(
                    self.style.WARNING(
                        f'⏰ Expired: {slot.teacher.name} - {slot.get_jalali_date()} {slot.start_time}-{slot.end_time}'
                    )
                )
        
        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(f'📊 Would expire {expired_count} slots (dry-run mode)')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'✅ Successfully expired {expired_count} slots')
            )
            
            # Show statistics
            expired_slots = TeacherAvailability.objects.filter(is_expired=True).count()
            available_slots = TeacherAvailability.objects.filter(
                is_expired=False,
                is_booked=False,
                is_available=True
            ).count()
            
            self.stdout.write(
                f'📈 Stats: {expired_slots} expired | {available_slots} available'
            )
