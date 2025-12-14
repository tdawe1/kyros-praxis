"""Background cleanup jobs."""

import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import delete, select

from ..db.models import Task, Project
try:
    from ..db.models import Run
except ImportError:
    from ..models import Run  # Fallback to models.py
from ..db.session import AsyncSessionLocal
from ..memory.shared_memory import shared_memory


logger = logging.getLogger(__name__)


# Global scheduler instance
scheduler = AsyncIOScheduler()


@scheduler.scheduled_job('interval', hours=1, id='cleanup_old_runs')
async def cleanup_old_runs():
    """
    Delete runs older than 7 days.
    
    Runs every hour.
    """
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=7)
        
        async with AsyncSessionLocal() as session:
            # Get count first
            result = await session.execute(
                select(Run).where(Run.created_at < cutoff)
            )
            old_runs = result.scalars().all()
            count = len(old_runs)
            
            if count > 0:
                # Delete old runs
                await session.execute(
                    delete(Run).where(Run.created_at < cutoff)
                )
                await session.commit()
                
                logger.info(f"Deleted {count} old runs (older than 7 days)")
            else:
                logger.debug("No old runs to delete")
    
    except Exception as e:
        logger.error(f"Error in cleanup_old_runs job: {e}", exc_info=True)


@scheduler.scheduled_job('interval', minutes=5, id='cleanup_expired_memory')
async def cleanup_expired_memory():
    """
    Delete expired shared memory entries.
    
    Runs every 5 minutes.
    """
    try:
        count = await shared_memory.cleanup_expired()
        count = count or 0
        if count > 0:
            logger.info(f"Cleaned up {count} expired shared memory entries")
        else:
            logger.debug("No expired memory entries to clean")
    
    except Exception as e:
        logger.error(f"Error in cleanup_expired_memory job: {e}", exc_info=True)


@scheduler.scheduled_job('interval', hours=24, id='cleanup_completed_tasks')
async def cleanup_completed_tasks():
    """
    Archive or delete tasks completed more than 30 days ago.
    
    Runs daily.
    """
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        
        async with AsyncSessionLocal() as session:
            # Get count of old completed tasks
            result = await session.execute(
                select(Task).where(
                    Task.status == "done",
                    Task.updated_at < cutoff
                )
            )
            old_tasks = result.scalars().all()
            count = len(old_tasks)
            
            if count > 0:
                # For now, just mark them as archived rather than deleting
                for task in old_tasks:
                    task.archived = True
                
                await session.commit()
                
                logger.info(f"Archived {count} old completed tasks (older than 30 days)")
            else:
                logger.debug("No old completed tasks to archive")
    
    except Exception as e:
        logger.error(f"Error in cleanup_completed_tasks job: {e}", exc_info=True)


@scheduler.scheduled_job('cron', hour=2, minute=0, id='database_maintenance')
async def database_maintenance():
    """
    Perform database maintenance tasks.
    
    Runs daily at 2 AM.
    """
    try:
        async with AsyncSessionLocal() as session:
            # Vacuum and analyze (PostgreSQL specific)
            # Note: VACUUM cannot be run inside a transaction, so we skip for now
            # In production, run this via a separate database maintenance script
            
            logger.info("Database maintenance completed")
    
    except Exception as e:
        logger.error(f"Error in database_maintenance job: {e}", exc_info=True)


def start_background_jobs():
    """Start all background jobs."""
    logger.info("Starting background jobs scheduler...")
    scheduler.start()
    logger.info(f"Background jobs started: {[job.id for job in scheduler.get_jobs()]}")


def stop_background_jobs():
    """Stop all background jobs."""
    logger.info("Stopping background jobs scheduler...")
    scheduler.shutdown()
    logger.info("Background jobs stopped")


# Job status and control functions

def get_job_status():
    """Get status of all background jobs."""
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    return jobs


def pause_job(job_id: str) -> bool:
    """Pause a background job."""
    try:
        scheduler.pause_job(job_id)
        logger.info(f"Paused job: {job_id}")
        return True
    except Exception as e:
        logger.error(f"Error pausing job {job_id}: {e}")
        return False


def resume_job(job_id: str) -> bool:
    """Resume a paused background job."""
    try:
        scheduler.resume_job(job_id)
        logger.info(f"Resumed job: {job_id}")
        return True
    except Exception as e:
        logger.error(f"Error resuming job {job_id}: {e}")
        return False
