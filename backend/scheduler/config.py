"""
APScheduler configuration and setup.

Configures the background scheduler for executing daily data refresh jobs
with timezone support and persistence.
"""

import os
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)


# Configuration parameters
SCHEDULER_TIMEZONE = os.getenv("SCHEDULER_TIMEZONE", "US/Eastern")
SCHEDULER_HOUR = int(os.getenv("SCHEDULER_HOUR", "5"))
SCHEDULER_MINUTE = int(os.getenv("SCHEDULER_MINUTE", "0"))
SCHEDULER_ENABLED = os.getenv("SCHEDULER_ENABLED", "true").lower() == "true"
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
DEFAULT_LEAGUE_AVG_ITT = float(os.getenv("DEFAULT_LEAGUE_AVG_ITT", "22.5"))


def create_scheduler() -> BackgroundScheduler:
    """
    Create and configure APScheduler instance.

    Configuration:
    - Timezone: US/Eastern (configurable via SCHEDULER_TIMEZONE)
    - Coalesce: True (skip missed jobs if previous still running)
    - Max instances: 1 (prevent overlapping job execution)

    Returns:
        Configured BackgroundScheduler instance
    """
    # Validate timezone
    try:
        import pytz
        pytz.timezone(SCHEDULER_TIMEZONE)
    except Exception as e:
        logger.warning(
            f"Invalid timezone {SCHEDULER_TIMEZONE}: {str(e)}. "
            f"Defaulting to US/Eastern."
        )
        timezone = "US/Eastern"
    else:
        timezone = SCHEDULER_TIMEZONE

    # Create scheduler
    scheduler = BackgroundScheduler(
        timezone=timezone,
        job_defaults={
            'coalesce': True,  # Skip missed jobs if previous still running
            'max_instances': 1,  # Only one instance of each job at a time
        }
    )

    # Configure logging
    logging.getLogger("apscheduler.executors.default").setLevel(logging.INFO)
    logging.getLogger("apscheduler.scheduler").setLevel(logging.INFO)

    logger.info(
        f"Scheduler configured: timezone={timezone}, "
        f"schedule={SCHEDULER_HOUR:02d}:{SCHEDULER_MINUTE:02d}, "
        f"enabled={SCHEDULER_ENABLED}"
    )

    return scheduler
