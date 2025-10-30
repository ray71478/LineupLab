"""
Scheduler startup and job registration.

Initializes APScheduler and registers daily data refresh job.
"""

import logging
import asyncio
from apscheduler.triggers.cron import CronTrigger

from backend.scheduler.config import (
    create_scheduler,
    SCHEDULER_HOUR,
    SCHEDULER_MINUTE,
    SCHEDULER_TIMEZONE,
    SCHEDULER_ENABLED,
)
from backend.scheduler.job_listener import JobListener

logger = logging.getLogger(__name__)


def wrap_async_job(async_func):
    """
    Wrap async function to run in event loop.

    Args:
        async_func: Async function to wrap

    Returns:
        Sync wrapper function
    """
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        finally:
            loop.close()
    return wrapper


def initialize_scheduler(get_db_func):
    """
    Initialize and start background scheduler.

    Creates scheduler instance, registers jobs, and starts execution.

    Args:
        get_db_func: Function that returns database session

    Returns:
        Initialized BackgroundScheduler instance, or None if disabled
    """
    if not SCHEDULER_ENABLED:
        logger.info("Scheduler is disabled via SCHEDULER_ENABLED environment variable")
        return None

    try:
        # Create scheduler
        scheduler = create_scheduler()

        # Register job listener
        listener = JobListener()
        scheduler.add_listener(
            listener.job_executed,
            mask=0x01  # EVENT_JOB_EXECUTED
        )
        scheduler.add_listener(
            listener.job_error,
            mask=0x20  # EVENT_JOB_ERROR
        )

        # Import here to avoid circular imports
        from backend.scheduler.daily_refresh_job import DailyDataRefreshJob

        # Create job function
        async def daily_refresh_job():
            """Execute daily data refresh."""
            db = get_db_func()
            try:
                job = DailyDataRefreshJob(db)
                result = await job.execute()

                if result.get("success"):
                    logger.info(
                        f"Daily refresh completed: "
                        f"Injuries={result.get('injuries', {}).get('stored', 0)}, "
                        f"Games={result.get('games', {}).get('stored', 0)}, "
                        f"TeamStats={result.get('team_stats', {}).get('stored', 0)}, "
                        f"Gamelogs={result.get('gamelogs', {}).get('stored', 0)}"
                    )
                else:
                    logger.error(
                        f"Daily refresh failed: {result.get('errors', [])}"
                    )
                return result
            finally:
                db.close()

        # Wrap async job for APScheduler (which expects sync functions)
        job_wrapper = wrap_async_job(daily_refresh_job)

        # Register cron job
        scheduler.add_job(
            job_wrapper,
            CronTrigger(
                hour=SCHEDULER_HOUR,
                minute=SCHEDULER_MINUTE,
                timezone=SCHEDULER_TIMEZONE
            ),
            id='daily_mysportsfeeds_refresh',
            name='Daily MySportsFeeds Data Refresh',
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )

        logger.info(
            f"Registered job: daily_mysportsfeeds_refresh "
            f"(scheduled for {SCHEDULER_HOUR:02d}:{SCHEDULER_MINUTE:02d} {SCHEDULER_TIMEZONE})"
        )

        # Start scheduler
        scheduler.start()
        logger.info("Scheduler started successfully")

        return scheduler

    except Exception as e:
        logger.error(f"Failed to initialize scheduler: {str(e)}", exc_info=True)
        return None


def shutdown_scheduler(scheduler):
    """
    Gracefully shutdown scheduler.

    Args:
        scheduler: BackgroundScheduler instance to shutdown
    """
    if scheduler and scheduler.running:
        try:
            logger.info("Shutting down scheduler...")
            scheduler.shutdown(wait=True)
            logger.info("Scheduler shut down gracefully")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {str(e)}")
