"""
APScheduler job listener for monitoring and logging job execution.

Tracks job success/failure events and logs execution metrics.
"""

import logging
from datetime import datetime
from apscheduler.events import JobExecutionEvent, JobSubmittedEvent, JobErrorEvent
from apscheduler.schedulers.base import SchedulerEvent

logger = logging.getLogger(__name__)


class JobListener:
    """Listener for APScheduler job events."""

    def __init__(self):
        """Initialize job listener."""
        self.logger = logger

    def job_submitted(self, event: JobSubmittedEvent) -> None:
        """Called when a job is submitted to the scheduler."""
        self.logger.debug(f"Job {event.job_id} submitted")

    def job_executed(self, event: JobExecutionEvent) -> None:
        """Called when a job completes successfully."""
        duration_ms = event.duration * 1000  # Convert to milliseconds
        self.logger.info(
            f"Job {event.job_id} executed successfully in {duration_ms:.0f}ms"
        )

    def job_error(self, event: JobErrorEvent) -> None:
        """Called when a job raises an exception."""
        self.logger.error(
            f"Job {event.job_id} failed with exception: {str(event.exception)}",
            exc_info=event.exception
        )

    def job_missed(self, event: SchedulerEvent) -> None:
        """Called when a job is missed (coalesced)."""
        self.logger.warning(f"Job {event.job_id} was missed (skipped)")
