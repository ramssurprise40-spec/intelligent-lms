"""
Database connection pooling configuration for production environments.

This module provides optimized database configurations for high-performance
and scalable deployments with connection pooling, read/write splitting,
and monitoring capabilities.
"""

import os
from django.core.exceptions import ImproperlyConfigured


def get_database_config():
    """
    Get database configuration based on environment.
    Supports connection pooling for production environments.
    """
    environment = os.getenv('DJANGO_ENV', 'development')
    
    # Base PostgreSQL configuration
    base_config = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DATABASE_NAME', 'intelligent_lms'),
        'USER': os.getenv('DATABASE_USER', 'lms_user'),
        'PASSWORD': os.getenv('DATABASE_PASSWORD', ''),
        'HOST': os.getenv('DATABASE_HOST', 'localhost'),
        'PORT': os.getenv('DATABASE_PORT', '5432'),
        'OPTIONS': {
            'sslmode': os.getenv('DATABASE_SSL_MODE', 'prefer'),
            'connect_timeout': 60,
        },
        'CONN_MAX_AGE': 0,  # Disable persistent connections when using pooling
    }
    
    if environment == 'production':
        # Production configuration with connection pooling
        return get_production_config(base_config)
    elif environment == 'staging':
        # Staging configuration with moderate pooling
        return get_staging_config(base_config)
    elif environment == 'testing':
        # Testing configuration
        return get_test_config()
    else:
        # Development configuration
        return get_development_config(base_config)


def get_production_config(base_config):
    """Production database configuration with connection pooling."""
    
    # Connection pooling options
    pool_options = {
        'MAX_CONNS': int(os.getenv('DATABASE_MAX_CONNS', '20')),
        'MIN_CONNS': int(os.getenv('DATABASE_MIN_CONNS', '5')),
        'MAX_LIFETIME': int(os.getenv('DATABASE_MAX_LIFETIME', '3600')),  # 1 hour
        'POOL_TIMEOUT': int(os.getenv('DATABASE_POOL_TIMEOUT', '30')),
        'POOL_RECYCLE': int(os.getenv('DATABASE_POOL_RECYCLE', '7200')),  # 2 hours
    }
    
    # Use django-db-connection-pool for production
    try:
        # Try using django-db-connection-pool if available
        import dj_db_conn_pool
        
        config = base_config.copy()
        config['ENGINE'] = 'dj_db_conn_pool.backends.postgresql'
        config['POOL_OPTIONS'] = {
            'POOL_SIZE': pool_options['MIN_CONNS'],
            'MAX_OVERFLOW': pool_options['MAX_CONNS'] - pool_options['MIN_CONNS'],
            'RECYCLE': pool_options['POOL_RECYCLE'],
            'TIMEOUT': pool_options['POOL_TIMEOUT'],
        }
        
        # Advanced PostgreSQL options for production
        config['OPTIONS'].update({
            'sslmode': 'require',
            'application_name': 'intelligent_lms_production',
            'connect_timeout': 30,
            'keepalives_idle': 600,
            'keepalives_interval': 30,
            'keepalives_count': 3,
        })
        
        return {
            'default': config,
            'read_replica': get_read_replica_config(config) if os.getenv('READ_REPLICA_HOST') else config
        }
        
    except ImportError:
        # Fallback to standard configuration with persistent connections
        config = base_config.copy()
        config['CONN_MAX_AGE'] = 300  # 5 minutes
        config['OPTIONS'].update({
            'sslmode': 'require',
            'application_name': 'intelligent_lms_production',
            'connect_timeout': 30,
        })
        
        return {'default': config}


def get_read_replica_config(primary_config):
    """Configuration for read replica database."""
    replica_config = primary_config.copy()
    replica_config.update({
        'HOST': os.getenv('READ_REPLICA_HOST'),
        'PORT': os.getenv('READ_REPLICA_PORT', '5432'),
        'USER': os.getenv('READ_REPLICA_USER', replica_config['USER']),
        'PASSWORD': os.getenv('READ_REPLICA_PASSWORD', replica_config['PASSWORD']),
    })
    replica_config['OPTIONS']['application_name'] = 'intelligent_lms_replica'
    return replica_config


def get_staging_config(base_config):
    """Staging environment configuration."""
    config = base_config.copy()
    config['CONN_MAX_AGE'] = 60  # 1 minute
    config['OPTIONS'].update({
        'application_name': 'intelligent_lms_staging',
        'connect_timeout': 30,
    })
    
    return {'default': config}


def get_development_config(base_config):
    """Development environment configuration."""
    # Check if PostgreSQL is available, fallback to SQLite
    try:
        import psycopg2
        postgres_available = True
    except ImportError:
        postgres_available = False
    
    if postgres_available and os.getenv('DATABASE_URL'):
        config = base_config.copy()
        config['CONN_MAX_AGE'] = 0  # No persistent connections in development
        config['OPTIONS']['application_name'] = 'intelligent_lms_dev'
        return {'default': config}
    else:
        # SQLite fallback for development
        return {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': os.path.join(os.path.dirname(os.path.dirname(__file__)), 'db.sqlite3'),
                'OPTIONS': {
                    'init_command': 'PRAGMA foreign_keys=1;',
                    'timeout': 20,
                },
            }
        }


def get_test_config():
    """Testing configuration using in-memory database."""
    return {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
            'OPTIONS': {
                'init_command': 'PRAGMA foreign_keys=1;',
            },
        }
    }


def get_monitoring_config():
    """
    Database monitoring and logging configuration.
    Used for tracking connection usage, slow queries, and performance metrics.
    """
    return {
        'LOGGING': {
            'version': 1,
            'disable_existing_loggers': False,
            'handlers': {
                'database_file': {
                    'level': 'INFO',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': os.path.join(os.getenv('LOG_DIR', 'logs'), 'database.log'),
                    'maxBytes': 1024*1024*5,  # 5 MB
                    'backupCount': 5,
                    'formatter': 'verbose',
                },
                'slow_query_file': {
                    'level': 'WARNING',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': os.path.join(os.getenv('LOG_DIR', 'logs'), 'slow_queries.log'),
                    'maxBytes': 1024*1024*5,  # 5 MB
                    'backupCount': 5,
                    'formatter': 'verbose',
                },
            },
            'loggers': {
                'django.db.backends': {
                    'handlers': ['database_file'],
                    'level': 'INFO' if os.getenv('DJANGO_ENV') == 'production' else 'DEBUG',
                    'propagate': False,
                },
                'django.db.backends.schema': {
                    'handlers': ['database_file'],
                    'level': 'INFO',
                    'propagate': False,
                },
            },
            'formatters': {
                'verbose': {
                    'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
                    'style': '{',
                },
            },
        }
    }


# Health check function for database connections
def check_database_health():
    """
    Perform basic health check on database connections.
    Returns dictionary with connection status and performance metrics.
    """
    from django.db import connections
    from django.core.management.color import no_style
    import time
    
    health_status = {}
    
    for alias in connections:
        try:
            start_time = time.time()
            connection = connections[alias]
            
            # Test connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()
            
            response_time = time.time() - start_time
            
            health_status[alias] = {
                'status': 'healthy',
                'response_time_ms': round(response_time * 1000, 2),
                'vendor': connection.vendor,
                'is_usable': connection.is_usable(),
            }
            
        except Exception as e:
            health_status[alias] = {
                'status': 'unhealthy',
                'error': str(e),
                'vendor': getattr(connection, 'vendor', 'unknown'),
                'is_usable': False,
            }
    
    return health_status


# Connection pool statistics (when using pooled connections)
def get_pool_statistics():
    """
    Get connection pool statistics if using pooled connections.
    Returns dictionary with pool metrics or None if not available.
    """
    try:
        from dj_db_conn_pool.core import pool_container
        
        stats = {}
        for alias, pool in pool_container._pools.items():
            stats[alias] = {
                'pool_size': pool.size(),
                'checked_out': pool.checkedout(),
                'overflow': pool.overflow(),
                'checked_in': pool.checkedin(),
            }
        
        return stats
        
    except (ImportError, AttributeError):
        return None


# Database initialization utilities
class DatabaseInitializer:
    """Utility class for database initialization and setup."""
    
    @staticmethod
    def enable_extensions():
        """Enable required PostgreSQL extensions."""
        from django.db import connection
        
        extensions = [
            'pgvector',  # Vector similarity search
            'pg_trgm',   # Trigram similarity for text search
            'btree_gin', # GIN indexes for better performance
            'btree_gist', # GiST indexes for spatial data
        ]
        
        try:
            with connection.cursor() as cursor:
                for extension in extensions:
                    try:
                        cursor.execute(f'CREATE EXTENSION IF NOT EXISTS {extension};')
                        print(f"✓ Extension '{extension}' enabled")
                    except Exception as e:
                        print(f"✗ Failed to enable extension '{extension}': {e}")
            
        except Exception as e:
            print(f"Database extensions setup failed: {e}")
    
    @staticmethod
    def create_indexes():
        """Create performance indexes for common queries."""
        from django.db import connection
        from django.core.management.color import no_style
        
        # Custom indexes for better performance
        custom_indexes = [
            # User activity indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS users_user_last_login_idx ON users_user (last_login DESC) WHERE last_login IS NOT NULL;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS users_user_role_active_idx ON users_user (role, is_active) WHERE is_active = true;",
            
            # Course search and filtering
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS courses_course_status_created_idx ON courses_course (status, created_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS courses_course_instructor_status_idx ON courses_course (instructor_id, status);",
            
            # Assessment performance
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS assessments_submission_student_submitted_idx ON assessments_submission (student_id, submitted_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS assessments_assessment_course_type_idx ON assessments_assessment (course_id, assessment_type);",
            
            # Communication indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS communications_post_topic_number_idx ON communications_post (topic_id, post_number);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS communications_message_thread_sent_idx ON communications_message (thread_id, sent_at) WHERE thread_id IS NOT NULL;",
        ]
        
        try:
            with connection.cursor() as cursor:
                for index_sql in custom_indexes:
                    try:
                        cursor.execute(index_sql)
                        print(f"✓ Index created: {index_sql.split()[-1]}")
                    except Exception as e:
                        print(f"✗ Failed to create index: {e}")
                        
        except Exception as e:
            print(f"Custom indexes creation failed: {e}")
