#backend/app/tasks/__init__.py

"""
Celery Tasks Module
Background tasks for asynchronous processing
"""

from celery import Celery
from app.config import settings

# Create Celery app
celery_app = Celery(
    'dashboard_tasks',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour
    task_soft_time_limit=3300,  # 55 minutes
)

# Import tasks
from .processing_tasks import (
    process_file_task,
    batch_process_files_task,
    cleanup_old_files_task
)

from .export_tasks import (
    export_chart_task,
    export_data_task,
    export_dashboard_task,
    cleanup_old_exports_task
)

__all__ = [
    "celery_app",
    # Processing tasks
    "process_file_task",
    "batch_process_files_task",
    "cleanup_old_files_task",
    # Export tasks
    "export_chart_task",
    "export_data_task",
    "export_dashboard_task",
    "cleanup_old_exports_task",
]