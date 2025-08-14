"""
Celery application configuration.

Sets up Celery for distributed task processing with Redis as broker.
"""

from celery import Celery
from kombu import Exchange, Queue

from modules.backend.core.config import settings
from modules.backend.config.logging_config import get_logger

logger = get_logger(__name__)

# Create Celery app
celery_app = Celery(
    "ai_dev_platform",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["src.backend.tasks"]
)

# Configure Celery
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_ignore_result=False,
    
    # Task routing
    task_routes={
        "agent.*": {"queue": "agents"},
        "orchestration.*": {"queue": "orchestration"},
        "cost_tracking.*": {"queue": "cost_tracking"},
    },
    
    # Queue configuration
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("agents", Exchange("agents"), routing_key="agent.*"),
        Queue("orchestration", Exchange("orchestration"), routing_key="orchestration.*"),
        Queue("cost_tracking", Exchange("cost_tracking"), routing_key="cost_tracking.*"),
    ),
    
    # Monitoring
    task_track_started=True,
    task_send_sent_event=True,
    
    # Error handling
    task_soft_time_limit=300,  # 5 minutes soft limit
    task_time_limit=600,  # 10 minutes hard limit
)

# Configure periodic tasks (if needed)
celery_app.conf.beat_schedule = {
    "cleanup-old-tasks": {
        "task": "orchestration.cleanup_completed_tasks",
        "schedule": 3600.0,  # Run every hour
    },
    "aggregate-costs": {
        "task": "cost_tracking.aggregate_daily_costs",
        "schedule": 86400.0,  # Run daily
    },
}

logger.info("Celery app configured", broker=settings.REDIS_URL) 