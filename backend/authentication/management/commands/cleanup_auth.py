"""
Management command to clean up old authentication data.

This command removes expired sessions, old login attempts, and outdated
security events to keep the database clean and performant.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from authentication.utils import (
    clean_expired_sessions,
    clean_old_login_attempts,
    clean_old_security_events
)


class Command(BaseCommand):
    help = 'Clean up old authentication data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days-login-attempts',
            type=int,
            default=30,
            help='Days to keep login attempts (default: 30)'
        )
        parser.add_argument(
            '--days-security-events',
            type=int,
            default=90,
            help='Days to keep security events (default: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned without actually doing it'
        )

    def handle(self, *args, **options):
        self.stdout.write("Starting authentication data cleanup...")
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING("DRY RUN MODE - No data will be deleted")
            )
        
        # Clean expired sessions
        try:
            session_count = clean_expired_sessions()
            if not options['dry_run']:
                self.stdout.write(
                    self.style.SUCCESS(f"Cleaned {session_count} expired sessions")
                )
            else:
                self.stdout.write(f"Would clean {session_count} expired sessions")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error cleaning sessions: {e}")
            )
        
        # Clean old login attempts
        try:
            if not options['dry_run']:
                attempts_count = clean_old_login_attempts()
                self.stdout.write(
                    self.style.SUCCESS(f"Cleaned {attempts_count} old login attempts")
                )
            else:
                from authentication.models import LoginAttempt
                cutoff_date = timezone.now() - timedelta(days=options['days_login_attempts'])
                count = LoginAttempt.objects.filter(attempted_at__lt=cutoff_date).count()
                self.stdout.write(f"Would clean {count} old login attempts")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error cleaning login attempts: {e}")
            )
        
        # Clean old security events
        try:
            if not options['dry_run']:
                events_count = clean_old_security_events()
                self.stdout.write(
                    self.style.SUCCESS(f"Cleaned {events_count} old security events")
                )
            else:
                from authentication.models import SecurityEvent
                cutoff_date = timezone.now() - timedelta(days=options['days_security_events'])
                count = SecurityEvent.objects.filter(
                    occurred_at__lt=cutoff_date,
                    risk_level__in=['low', 'medium']
                ).count()
                self.stdout.write(f"Would clean {count} old security events")
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error cleaning security events: {e}")
            )
        
        self.stdout.write(
            self.style.SUCCESS("Authentication data cleanup completed!")
        )
