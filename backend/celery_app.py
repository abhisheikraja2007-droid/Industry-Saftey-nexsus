"""
Celery application for background task processing.
Tasks: LLM incident report generation, alert notifications, data archival.
"""
from __future__ import annotations
import os
import sys
import logging

# Ensure project packages are importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "industrial_safety",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["celery_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)

logger = logging.getLogger(__name__)
logger.info("Celery app initialised with broker: %s", REDIS_URL)
