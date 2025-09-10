"""
Task queue monitoring and management utilities for Intelligent LMS.
"""

import redis
import json
from celery import Celery
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class TaskQueueMonitor:
    """Monitor and manage Celery and Dramatiq task queues."""
    
    def __init__(self):
        self.redis_client = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        self.celery_app = Celery('intelligent_lms')
        self.celery_app.config_from_object('django.conf:settings', namespace='CELERY')
    
    def get_queue_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics for all queues."""
        try:
            stats = {}
            
            # Celery queues
            celery_queues = [
                'default', 'user_tasks', 'course_tasks', 'assessment_tasks',
                'communication_tasks', 'analytics_tasks', 'system_tasks',
                'ai_content', 'ai_assessment', 'ai_communication',
                'high_priority', 'low_priority'
            ]
            
            for queue in celery_queues:
                queue_length = self.redis_client.llen(queue)
                stats[queue] = {
                    'type': 'celery',
                    'pending_tasks': queue_length,
                    'status': 'healthy' if queue_length < 1000 else 'high_load'
                }
            
            # Dramatiq queues
            dramatiq_queues = [
                'intelligent_lms:ai_content',
                'intelligent_lms:ai_assessment',
                'intelligent_lms:search',
                'intelligent_lms:analytics',
                'intelligent_lms:file_processing',
                'intelligent_lms:notifications'
            ]
            
            for queue in dramatiq_queues:
                queue_length = self.redis_client.llen(queue)
                stats[queue.split(':')[1]] = {
                    'type': 'dramatiq',
                    'pending_tasks': queue_length,
                    'status': 'healthy' if queue_length < 500 else 'high_load'
                }
            
            # Overall system health
            total_pending = sum(queue_data['pending_tasks'] for queue_data in stats.values())
            system_status = 'healthy'
            if total_pending > 5000:
                system_status = 'critical'
            elif total_pending > 2000:
                system_status = 'high_load'
            elif total_pending > 1000:
                system_status = 'moderate_load'
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_pending_tasks': total_pending,
                'system_status': system_status,
                'queues': stats
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue stats: {e}")
            return {'error': str(e)}
    
    def get_worker_stats(self) -> Dict[str, Any]:
        """Get active worker statistics."""
        try:
            inspect = self.celery_app.control.inspect()
            
            # Get active workers
            active_workers = inspect.active() or {}
            
            # Get worker statistics
            stats = inspect.stats() or {}
            
            # Get scheduled tasks
            scheduled = inspect.scheduled() or {}
            
            # Get reserved tasks
            reserved = inspect.reserved() or {}
            
            worker_info = {}
            for worker_name in active_workers.keys():
                worker_info[worker_name] = {
                    'status': 'active',
                    'active_tasks': len(active_workers.get(worker_name, [])),
                    'scheduled_tasks': len(scheduled.get(worker_name, [])),
                    'reserved_tasks': len(reserved.get(worker_name, [])),
                    'stats': stats.get(worker_name, {})
                }
            
            return {
                'timestamp': datetime.now().isoformat(),
                'total_workers': len(active_workers),
                'workers': worker_info
            }
            
        except Exception as e:
            logger.error(f"Failed to get worker stats: {e}")
            return {'error': str(e)}
    
    def get_failed_tasks(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent failed tasks."""
        try:
            # This would need to be implemented based on your result backend
            # For now, return a placeholder structure
            return []
            
        except Exception as e:
            logger.error(f"Failed to get failed tasks: {e}")
            return []
    
    def purge_queue(self, queue_name: str) -> Dict[str, Any]:
        """Purge all tasks from a specific queue."""
        try:
            purged_count = self.celery_app.control.purge()
            
            return {
                'queue_name': queue_name,
                'purged_tasks': purged_count,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to purge queue {queue_name}: {e}")
            return {'error': str(e)}
    
    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """Cancel a specific task."""
        try:
            self.celery_app.control.revoke(task_id, terminate=True)
            
            return {
                'task_id': task_id,
                'status': 'cancelled',
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return {'error': str(e)}
    
    def get_task_history(self, hours: int = 24) -> Dict[str, Any]:
        """Get task execution history."""
        try:
            # This would need to be implemented based on your monitoring setup
            # For now, return a placeholder structure
            return {
                'period_hours': hours,
                'total_executed': 0,
                'successful': 0,
                'failed': 0,
                'retried': 0,
                'average_execution_time': 0,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get task history: {e}")
            return {'error': str(e)}


class TaskHealthChecker:
    """Health checking utilities for the task queue system."""
    
    def __init__(self):
        self.monitor = TaskQueueMonitor()
    
    def check_system_health(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'checks': {}
        }
        
        # Check Redis connectivity
        try:
            self.monitor.redis_client.ping()
            health_status['checks']['redis'] = {
                'status': 'healthy',
                'message': 'Redis connection successful'
            }
        except Exception as e:
            health_status['checks']['redis'] = {
                'status': 'unhealthy',
                'message': f'Redis connection failed: {str(e)}'
            }
            health_status['overall_status'] = 'unhealthy'
        
        # Check queue lengths
        queue_stats = self.monitor.get_queue_stats()
        if 'error' in queue_stats:
            health_status['checks']['queues'] = {
                'status': 'unhealthy',
                'message': f'Failed to get queue stats: {queue_stats["error"]}'
            }
            health_status['overall_status'] = 'unhealthy'
        else:
            critical_queues = [
                name for name, data in queue_stats['queues'].items()
                if data['status'] == 'critical'
            ]
            if critical_queues:
                health_status['checks']['queues'] = {
                    'status': 'critical',
                    'message': f'Critical queue load detected: {critical_queues}'
                }
                health_status['overall_status'] = 'critical'
            elif queue_stats['system_status'] != 'healthy':
                health_status['checks']['queues'] = {
                    'status': 'warning',
                    'message': f'System status: {queue_stats["system_status"]}'
                }
                if health_status['overall_status'] == 'healthy':
                    health_status['overall_status'] = 'warning'
            else:
                health_status['checks']['queues'] = {
                    'status': 'healthy',
                    'message': 'All queues operating normally'
                }
        
        # Check worker availability
        worker_stats = self.monitor.get_worker_stats()
        if 'error' in worker_stats:
            health_status['checks']['workers'] = {
                'status': 'unhealthy',
                'message': f'Failed to get worker stats: {worker_stats["error"]}'
            }
            health_status['overall_status'] = 'unhealthy'
        else:
            if worker_stats['total_workers'] == 0:
                health_status['checks']['workers'] = {
                    'status': 'critical',
                    'message': 'No active workers detected'
                }
                health_status['overall_status'] = 'critical'
            elif worker_stats['total_workers'] < 3:
                health_status['checks']['workers'] = {
                    'status': 'warning',
                    'message': f'Low worker count: {worker_stats["total_workers"]}'
                }
                if health_status['overall_status'] == 'healthy':
                    health_status['overall_status'] = 'warning'
            else:
                health_status['checks']['workers'] = {
                    'status': 'healthy',
                    'message': f'{worker_stats["total_workers"]} workers active'
                }
        
        return health_status
    
    def check_queue_health(self, queue_name: str) -> Dict[str, Any]:
        """Check health of a specific queue."""
        try:
            queue_length = self.monitor.redis_client.llen(queue_name)
            
            status = 'healthy'
            if queue_length > 1000:
                status = 'critical'
            elif queue_length > 500:
                status = 'warning'
            
            return {
                'queue_name': queue_name,
                'status': status,
                'pending_tasks': queue_length,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'queue_name': queue_name,
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


class TaskPerformanceAnalyzer:
    """Analyze task performance and provide optimization suggestions."""
    
    def __init__(self):
        self.monitor = TaskQueueMonitor()
    
    def analyze_queue_performance(self) -> Dict[str, Any]:
        """Analyze queue performance and suggest optimizations."""
        try:
            stats = self.monitor.get_queue_stats()
            
            if 'error' in stats:
                return {'error': stats['error']}
            
            analysis = {
                'timestamp': datetime.now().isoformat(),
                'recommendations': []
            }
            
            # Analyze each queue
            for queue_name, queue_data in stats['queues'].items():
                pending = queue_data['pending_tasks']
                
                if pending > 1000:
                    analysis['recommendations'].append({
                        'priority': 'high',
                        'queue': queue_name,
                        'issue': 'High queue backlog',
                        'suggestion': 'Increase worker concurrency or add more workers'
                    })
                elif pending > 500:
                    analysis['recommendations'].append({
                        'priority': 'medium',
                        'queue': queue_name,
                        'issue': 'Moderate queue backlog',
                        'suggestion': 'Monitor queue and consider scaling if trend continues'
                    })
            
            # System-wide recommendations
            if stats['total_pending_tasks'] > 5000:
                analysis['recommendations'].append({
                    'priority': 'critical',
                    'queue': 'system',
                    'issue': 'Critical system load',
                    'suggestion': 'Immediate scaling required - add workers and review task efficiency'
                })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze queue performance: {e}")
            return {'error': str(e)}
    
    def get_optimization_suggestions(self) -> List[Dict[str, str]]:
        """Get general optimization suggestions for the task queue system."""
        return [
            {
                'category': 'Worker Configuration',
                'suggestion': 'Use separate workers for CPU-intensive and I/O-bound tasks',
                'impact': 'Improves overall throughput and reduces blocking'
            },
            {
                'category': 'Queue Management',
                'suggestion': 'Implement priority queues for time-sensitive tasks',
                'impact': 'Ensures critical tasks are processed first'
            },
            {
                'category': 'Error Handling',
                'suggestion': 'Use exponential backoff for task retries',
                'impact': 'Reduces system load during failures'
            },
            {
                'category': 'Monitoring',
                'suggestion': 'Set up alerts for queue length thresholds',
                'impact': 'Enables proactive scaling and issue detection'
            },
            {
                'category': 'Resource Optimization',
                'suggestion': 'Monitor memory usage and implement task result expiration',
                'impact': 'Prevents memory leaks and reduces Redis memory usage'
            }
        ]


# Convenience functions for common monitoring tasks
def get_system_status() -> Dict[str, Any]:
    """Quick system status check."""
    monitor = TaskQueueMonitor()
    health_checker = TaskHealthChecker()
    
    return {
        'queue_stats': monitor.get_queue_stats(),
        'worker_stats': monitor.get_worker_stats(),
        'health_check': health_checker.check_system_health()
    }


def get_performance_report() -> Dict[str, Any]:
    """Generate comprehensive performance report."""
    analyzer = TaskPerformanceAnalyzer()
    
    return {
        'performance_analysis': analyzer.analyze_queue_performance(),
        'optimization_suggestions': analyzer.get_optimization_suggestions()
    }
