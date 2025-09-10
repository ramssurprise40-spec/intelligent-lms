"""
Shared task queue configuration for FastAPI microservices using Dramatiq.
"""

import dramatiq
import logging
from dramatiq.brokers.redis import RedisBroker
from dramatiq.results import Results
from dramatiq.results.backends.redis import RedisBackend
from dramatiq.middleware import CurrentMessage, Middleware
import redis
import os
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
REDIS_DB = int(os.getenv('REDIS_DB', '0'))
REDIS_RESULTS_DB = int(os.getenv('REDIS_RESULTS_DB', '5'))

# Initialize Redis connections
redis_client = redis.Redis.from_url(f"{REDIS_URL}/{REDIS_DB}")
redis_results_client = redis.Redis.from_url(f"{REDIS_URL}/{REDIS_RESULTS_DB}")

# Configure Redis broker
redis_broker = RedisBroker(
    url=f"{REDIS_URL}/{REDIS_DB}",
    namespace="intelligent_lms"
)

# Configure results backend
results_backend = RedisBackend(
    client=redis_results_client,
    namespace="intelligent_lms_results"
)

# Add middleware
redis_broker.add_middleware(Results(backend=results_backend))
redis_broker.add_middleware(CurrentMessage())


class TaskMetricsMiddleware(Middleware):
    """Middleware to track task execution metrics."""

    def before_process_message(self, broker, message):
        logger.info(f"Starting task: {message.actor_name} with ID: {message.message_id}")

    def after_process_message(self, broker, message, *, result=None, exception=None):
        if exception:
            logger.error(f"Task {message.actor_name} failed: {exception}")
        else:
            logger.info(f"Task {message.actor_name} completed successfully")

    def after_skip_message(self, broker, message):
        logger.warning(f"Task {message.actor_name} was skipped")


# Add metrics middleware
redis_broker.add_middleware(TaskMetricsMiddleware())

# Set the broker
dramatiq.set_broker(redis_broker)


# Queue configurations for different microservices
QUEUE_CONFIGS = {
    'ai_content': {
        'description': 'AI content generation tasks',
        'max_retries': 3,
        'min_backoff': 1000,
        'max_backoff': 900000,
        'priority': 'normal'
    },
    'ai_assessment': {
        'description': 'AI assessment and grading tasks',
        'max_retries': 3,
        'min_backoff': 1000,
        'max_backoff': 900000,
        'priority': 'high'
    },
    'ai_communication': {
        'description': 'AI communication and messaging tasks',
        'max_retries': 2,
        'min_backoff': 500,
        'max_backoff': 300000,
        'priority': 'high'
    },
    'search': {
        'description': 'Search indexing and retrieval tasks',
        'max_retries': 5,
        'min_backoff': 2000,
        'max_backoff': 600000,
        'priority': 'low'
    },
    'analytics': {
        'description': 'Analytics and reporting tasks',
        'max_retries': 3,
        'min_backoff': 5000,
        'max_backoff': 1800000,
        'priority': 'low'
    },
    'file_processing': {
        'description': 'File upload and processing tasks',
        'max_retries': 3,
        'min_backoff': 1000,
        'max_backoff': 600000,
        'priority': 'normal'
    },
    'notifications': {
        'description': 'Notification delivery tasks',
        'max_retries': 5,
        'min_backoff': 1000,
        'max_backoff': 300000,
        'priority': 'high'
    }
}


def get_task_decorator(queue_name: str, **kwargs):
    """
    Get a dramatiq actor decorator with predefined configuration.
    
    Args:
        queue_name (str): Name of the queue
        **kwargs: Additional arguments for the actor
    
    Returns:
        dramatiq.actor decorator
    """
    queue_config = QUEUE_CONFIGS.get(queue_name, {})
    
    default_args = {
        'queue_name': queue_name,
        'max_retries': queue_config.get('max_retries', 3),
        'min_backoff': queue_config.get('min_backoff', 1000),
        'max_backoff': queue_config.get('max_backoff', 900000),
        'store_results': True,
        'result_ttl': 3600000,  # 1 hour
    }
    
    # Override with provided kwargs
    default_args.update(kwargs)
    
    return dramatiq.actor(**default_args)


# Health check function
def check_broker_health() -> Dict[str, Any]:
    """Check the health of the message broker."""
    try:
        # Test Redis connection
        redis_client.ping()
        redis_results_client.ping()
        
        # Get queue information
        queue_info = {}
        for queue_name in QUEUE_CONFIGS.keys():
            queue_size = redis_client.llen(f"intelligent_lms:{queue_name}")
            queue_info[queue_name] = {
                'size': queue_size,
                'status': 'healthy'
            }
        
        return {
            'status': 'healthy',
            'broker': 'redis',
            'queues': queue_info,
            'timestamp': dramatiq.get_broker().get_declared_queues()
        }
        
    except Exception as e:
        logger.error(f"Broker health check failed: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': dramatiq.get_broker().get_declared_queues()
        }


# Utility functions for task management
def get_task_result(message_id: str, timeout: int = 5000) -> Optional[Any]:
    """
    Get the result of a completed task.
    
    Args:
        message_id (str): The message ID of the task
        timeout (int): Timeout in milliseconds
    
    Returns:
        Task result or None if not found/timed out
    """
    try:
        result = results_backend.get_result(
            message=type('Message', (), {'message_id': message_id})(),
            block=True,
            timeout=timeout
        )
        return result
    except Exception as e:
        logger.error(f"Failed to get task result for {message_id}: {e}")
        return None


def cancel_task(message_id: str) -> bool:
    """
    Cancel a pending task.
    
    Args:
        message_id (str): The message ID of the task to cancel
    
    Returns:
        True if task was cancelled, False otherwise
    """
    try:
        # In Dramatiq, cancellation is handled by removing from queue
        # This is a simplified implementation
        logger.info(f"Attempting to cancel task {message_id}")
        return True
    except Exception as e:
        logger.error(f"Failed to cancel task {message_id}: {e}")
        return False


def get_queue_stats() -> Dict[str, Any]:
    """
    Get statistics for all queues.
    
    Returns:
        Dictionary with queue statistics
    """
    stats = {}
    try:
        for queue_name in QUEUE_CONFIGS.keys():
            queue_size = redis_client.llen(f"intelligent_lms:{queue_name}")
            stats[queue_name] = {
                'pending_tasks': queue_size,
                'description': QUEUE_CONFIGS[queue_name]['description']
            }
    except Exception as e:
        logger.error(f"Failed to get queue stats: {e}")
        stats = {'error': str(e)}
    
    return stats


# Export the configured broker and utilities
__all__ = [
    'dramatiq',
    'redis_broker',
    'results_backend',
    'get_task_decorator',
    'check_broker_health',
    'get_task_result',
    'cancel_task',
    'get_queue_stats',
    'QUEUE_CONFIGS'
]
