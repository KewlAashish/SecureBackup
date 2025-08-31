from __future__ import annotations
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from typing import Callable, Dict

### CHANGE ###
# Use tzlocal to make the scheduler timezone-aware
from tzlocal import get_localzone

class BackupScheduler:
    def __init__(self):
        ### CHANGE ###
        # Initialize scheduler with local timezone and store multiple jobs
        self._sched = BackgroundScheduler(timezone=str(get_localzone()))
        self._jobs: Dict[str, any] = {}

    def start(self):
        if not self._sched.running:
            self._sched.start()

    def stop(self):
        if self._sched.running:
            self._sched.shutdown(wait=False)

    ### CHANGE ###
    # New method to add/update a specific job by ID (we'll use the job name)
    def add_or_update_job(self, job_id: str, cron_expr: str, fn: Callable, *args, **kwargs):
        self.remove_job(job_id) # Remove existing job if it exists
        trigger = CronTrigger.from_crontab(cron_expr)
        job = self._sched.add_job(fn, trigger, args=args, kwargs=kwargs, id=job_id, coalesce=True, max_instances=1)
        self._jobs[job_id] = job

    ### CHANGE ###
    # New method to remove a job by ID
    def remove_job(self, job_id: str):
        if job_id in self._jobs:
            self._sched.remove_job(job_id)
            del self._jobs[job_id]
            
    ### CHANGE ###
    # Moved cron generation logic here to keep it self-contained
    @staticmethod
    def cron_from_job(job: dict) -> str:
        hour, minute = job.get("time", "10:00").split(":")
        freq = job.get("frequency", "Daily")
        
        if freq == "Daily":
            return f"{minute} {hour} * * *"
        elif freq == "Weekly":
            dow = job.get("day", "Monday")
            days = {"Sunday":"0", "Monday":"1", "Tuesday":"2", "Wednesday":"3", "Thursday":"4", "Friday":"5", "Saturday":"6"}
            return f"{minute} {hour} * * {days.get(dow, '1')}"
        # Add other frequencies like Monthly if needed
        return f"{minute} {hour} * * *"