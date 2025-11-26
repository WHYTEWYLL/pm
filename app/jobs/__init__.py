"""Background jobs package.

Modules:
- celery: Celery app configuration and beat schedule
- sync: Data ingestion tasks (Slack, Linear, GitHub)
- workflows: Automated workflow tasks (standups, etc.)
"""

from .celery import celery_app

__all__ = ["celery_app"]
