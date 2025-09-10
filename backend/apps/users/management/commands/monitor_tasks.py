"""
Django management command for monitoring and managing task queues.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from intelligent_lms.task_monitor import (
    TaskQueueMonitor, TaskHealthChecker, TaskPerformanceAnalyzer,
    get_system_status, get_performance_report
)
import json
from datetime import datetime


class Command(BaseCommand):
    help = 'Monitor and manage Celery and Dramatiq task queues'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['status', 'health', 'performance', 'workers', 'purge', 'cancel'],
            default='status',
            help='Action to perform'
        )
        
        parser.add_argument(
            '--queue',
            type=str,
            help='Specific queue name for queue-specific operations'
        )
        
        parser.add_argument(
            '--task-id',
            type=str,
            help='Task ID for task-specific operations'
        )
        
        parser.add_argument(
            '--format',
            type=str,
            choices=['json', 'table', 'summary'],
            default='table',
            help='Output format'
        )
        
        parser.add_argument(
            '--watch',
            action='store_true',
            help='Watch mode - continuously display status'
        )
        
        parser.add_argument(
            '--interval',
            type=int,
            default=5,
            help='Watch interval in seconds'
        )

    def handle(self, *args, **options):
        action = options['action']
        output_format = options['format']
        
        try:
            if action == 'status':
                self.handle_status(options, output_format)
            elif action == 'health':
                self.handle_health(options, output_format)
            elif action == 'performance':
                self.handle_performance(options, output_format)
            elif action == 'workers':
                self.handle_workers(options, output_format)
            elif action == 'purge':
                self.handle_purge(options, output_format)
            elif action == 'cancel':
                self.handle_cancel(options, output_format)
                
        except Exception as e:
            raise CommandError(f'Command failed: {e}')

    def handle_status(self, options, output_format):
        """Handle queue status display."""
        monitor = TaskQueueMonitor()
        
        if options['watch']:
            self.watch_status(monitor, options['interval'], output_format)
        else:
            stats = monitor.get_queue_stats()
            self.display_output(stats, output_format, 'Queue Status')

    def handle_health(self, options, output_format):
        """Handle system health check."""
        health_checker = TaskHealthChecker()
        
        if options['queue']:
            health_data = health_checker.check_queue_health(options['queue'])
            self.display_output(health_data, output_format, f'Queue Health: {options["queue"]}')
        else:
            health_data = health_checker.check_system_health()
            self.display_output(health_data, output_format, 'System Health')

    def handle_performance(self, options, output_format):
        """Handle performance analysis."""
        report = get_performance_report()
        self.display_output(report, output_format, 'Performance Report')

    def handle_workers(self, options, output_format):
        """Handle worker status display."""
        monitor = TaskQueueMonitor()
        worker_stats = monitor.get_worker_stats()
        self.display_output(worker_stats, output_format, 'Worker Status')

    def handle_purge(self, options, output_format):
        """Handle queue purging."""
        if not options['queue']:
            raise CommandError('--queue is required for purge action')
        
        if not self.confirm_action(f'purge queue "{options["queue"]}"'):
            self.stdout.write('Operation cancelled.')
            return
            
        monitor = TaskQueueMonitor()
        result = monitor.purge_queue(options['queue'])
        self.display_output(result, output_format, 'Purge Result')

    def handle_cancel(self, options, output_format):
        """Handle task cancellation."""
        if not options['task_id']:
            raise CommandError('--task-id is required for cancel action')
        
        if not self.confirm_action(f'cancel task "{options["task_id"]}"'):
            self.stdout.write('Operation cancelled.')
            return
            
        monitor = TaskQueueMonitor()
        result = monitor.cancel_task(options['task_id'])
        self.display_output(result, output_format, 'Cancel Result')

    def watch_status(self, monitor, interval, output_format):
        """Watch mode for continuous status display."""
        import time
        import os
        
        try:
            while True:
                # Clear screen (works on most terminals)
                os.system('cls' if os.name == 'nt' else 'clear')
                
                stats = monitor.get_queue_stats()
                self.display_output(stats, output_format, f'Queue Status (Updated: {datetime.now().strftime("%H:%M:%S")})')
                
                self.stdout.write(f'\nRefreshing in {interval} seconds... (Press Ctrl+C to stop)')
                time.sleep(interval)
                
        except KeyboardInterrupt:
            self.stdout.write('\nWatch mode stopped.')

    def display_output(self, data, output_format, title):
        """Display output in the specified format."""
        self.stdout.write(self.style.SUCCESS(f'\n=== {title} ===\n'))
        
        if output_format == 'json':
            self.stdout.write(json.dumps(data, indent=2, default=str))
        elif output_format == 'table':
            self.display_table_format(data)
        elif output_format == 'summary':
            self.display_summary_format(data)

    def display_table_format(self, data):
        """Display data in table format."""
        if 'queues' in data:
            # Queue status table
            self.stdout.write(f"{'Queue Name':<20} {'Type':<10} {'Pending':<10} {'Status':<15}")
            self.stdout.write('-' * 60)
            
            for queue_name, queue_data in data['queues'].items():
                status_style = self.style.SUCCESS if queue_data['status'] == 'healthy' else self.style.WARNING
                self.stdout.write(
                    f"{queue_name:<20} {queue_data['type']:<10} {queue_data['pending_tasks']:<10} "
                    f"{status_style(queue_data['status']):<15}"
                )
            
            self.stdout.write(f"\nTotal pending tasks: {data['total_pending_tasks']}")
            self.stdout.write(f"System status: {self.get_styled_status(data['system_status'])}")
            
        elif 'workers' in data:
            # Worker status table
            self.stdout.write(f"{'Worker Name':<30} {'Status':<10} {'Active':<8} {'Scheduled':<10} {'Reserved':<10}")
            self.stdout.write('-' * 75)
            
            for worker_name, worker_data in data['workers'].items():
                self.stdout.write(
                    f"{worker_name:<30} {worker_data['status']:<10} "
                    f"{worker_data['active_tasks']:<8} {worker_data['scheduled_tasks']:<10} "
                    f"{worker_data['reserved_tasks']:<10}"
                )
            
            self.stdout.write(f"\nTotal workers: {data['total_workers']}")
            
        elif 'checks' in data:
            # Health check table
            self.stdout.write(f"{'Component':<15} {'Status':<12} {'Message'}")
            self.stdout.write('-' * 60)
            
            for component, check_data in data['checks'].items():
                status_style = self.get_styled_status(check_data['status'])
                self.stdout.write(f"{component:<15} {status_style(check_data['status']):<12} {check_data['message']}")
            
            self.stdout.write(f"\nOverall status: {self.get_styled_status(data['overall_status'])}")
            
        else:
            # Generic key-value display
            for key, value in data.items():
                if isinstance(value, dict):
                    self.stdout.write(f"{key}:")
                    for sub_key, sub_value in value.items():
                        self.stdout.write(f"  {sub_key}: {sub_value}")
                else:
                    self.stdout.write(f"{key}: {value}")

    def display_summary_format(self, data):
        """Display data in summary format."""
        if 'queues' in data:
            total_pending = data['total_pending_tasks']
            active_queues = len([q for q in data['queues'].values() if q['pending_tasks'] > 0])
            
            self.stdout.write(f"📊 System Overview:")
            self.stdout.write(f"   • Total pending tasks: {total_pending}")
            self.stdout.write(f"   • Active queues: {active_queues}/{len(data['queues'])}")
            self.stdout.write(f"   • System status: {self.get_styled_status(data['system_status'])}")
            
            if total_pending > 0:
                self.stdout.write(f"\n🔥 Busiest queues:")
                sorted_queues = sorted(
                    data['queues'].items(), 
                    key=lambda x: x[1]['pending_tasks'], 
                    reverse=True
                )
                
                for queue_name, queue_data in sorted_queues[:5]:
                    if queue_data['pending_tasks'] > 0:
                        self.stdout.write(f"   • {queue_name}: {queue_data['pending_tasks']} tasks")
                        
        elif 'overall_status' in data:
            self.stdout.write(f"🏥 Health Summary:")
            self.stdout.write(f"   • Overall status: {self.get_styled_status(data['overall_status'])}")
            
            for component, check_data in data['checks'].items():
                status_icon = '✅' if check_data['status'] == 'healthy' else '❌'
                self.stdout.write(f"   {status_icon} {component}: {check_data['status']}")

    def get_styled_status(self, status):
        """Get styled status text."""
        if status in ['healthy', 'success']:
            return self.style.SUCCESS(status)
        elif status in ['warning', 'moderate_load']:
            return self.style.WARNING(status)
        elif status in ['critical', 'unhealthy', 'high_load']:
            return self.style.ERROR(status)
        else:
            return status

    def confirm_action(self, action_description):
        """Confirm destructive actions."""
        response = input(f'Are you sure you want to {action_description}? [y/N]: ')
        return response.lower() in ['y', 'yes']
