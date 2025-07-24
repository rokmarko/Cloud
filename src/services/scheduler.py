"""
Background task scheduler for KanardiaCloud
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from flask import Flask
from src.services.thingsboard_sync import thingsboard_sync


logger = logging.getLogger(__name__)


class BackgroundTaskScheduler:
    """Background task scheduler using APScheduler."""
    
    def __init__(self, app: Flask = None):
        self.scheduler = None
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize the scheduler with Flask app."""
        self.app = app
        
        # Configure scheduler
        self.scheduler = BackgroundScheduler(
            daemon=True,
            timezone='UTC'
        )
        
        # Add jobs
        self._add_jobs()
        
        # Start scheduler
        self.start()
        
        # Register shutdown handler
        import atexit
        atexit.register(self.shutdown)
        
        logger.info("Background task scheduler initialized")
    
    def _add_jobs(self):
        """Add scheduled jobs."""
        if not self.scheduler:
            return
        
        # Add ThingsBoard sync job - runs every 5 minutes
        self.scheduler.add_job(
            func=self._sync_thingsboard_job,
            trigger=IntervalTrigger(minutes=5),
            id='thingsboard_sync',
            name='ThingsBoard Logbook Sync',
            replace_existing=True,
            max_instances=1  # Prevent overlapping runs
        )
        
        logger.info("Scheduled ThingsBoard sync job to run every 5 minutes")
    
    def _sync_thingsboard_job(self):
        """Background job to sync logbook entries from ThingsBoard."""
        try:
            logger.info("Starting ThingsBoard sync job")
            
            # Create app context for database operations
            with self.app.app_context():
                results = thingsboard_sync.sync_all_devices()
                
                # Log results
                if results['errors']:
                    logger.warning(f"ThingsBoard sync completed with errors: {results}")
                else:
                    logger.info(f"ThingsBoard sync completed successfully: "
                              f"{results['synced_devices']}/{results['total_devices']} devices, "
                              f"{results['new_entries']} new entries")
                
        except Exception as e:
            logger.error(f"Fatal error in ThingsBoard sync job: {str(e)}", exc_info=True)
    
    def start(self):
        """Start the scheduler."""
        if self.scheduler and not self.scheduler.running:
            self.scheduler.start()
            logger.info("Background task scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Background task scheduler shutdown")
    
    def get_jobs(self):
        """Get all scheduled jobs."""
        if self.scheduler:
            return self.scheduler.get_jobs()
        return []
    
    def pause_job(self, job_id: str):
        """Pause a specific job."""
        if self.scheduler:
            self.scheduler.pause_job(job_id)
            logger.info(f"Paused job: {job_id}")
    
    def resume_job(self, job_id: str):
        """Resume a specific job."""
        if self.scheduler:
            self.scheduler.resume_job(job_id)
            logger.info(f"Resumed job: {job_id}")
    
    def remove_job(self, job_id: str):
        """Remove a specific job."""
        if self.scheduler:
            self.scheduler.remove_job(job_id)
            logger.info(f"Removed job: {job_id}")


# Create singleton instance
task_scheduler = BackgroundTaskScheduler()
