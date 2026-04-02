import os
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

os.environ.setdefault("FLASK_ENV", "production")

from app.main import create_app

app = create_app()
scheduler = BlockingScheduler(timezone=app.config.get("SCHEDULER_TIMEZONE", "UTC"))


def with_context(fn):
    def wrapper(*args, **kwargs):
        with app.app_context():
            return fn(*args, **kwargs)
    wrapper.__name__ = fn.__name__
    return wrapper


@with_context
def evaluate_alerts():
    from app.workers.jobs.evaluate_alerts import run_alert_evaluation
    run_alert_evaluation()


@with_context
def anomaly_detection():
    from app.workers.jobs.run_ai_analysis import run_anomaly_detection
    run_anomaly_detection()


@with_context
def weekly_summary():
    from app.workers.jobs.run_ai_analysis import run_weekly_summary
    run_weekly_summary()


@with_context
def prune_data():
    from app.workers.jobs.prune_old_data import run_prune
    run_prune()


scheduler.add_job(evaluate_alerts, IntervalTrigger(seconds=60), id="evaluate_alerts", replace_existing=True)
scheduler.add_job(anomaly_detection, CronTrigger(hour=3, minute=0), id="anomaly_detection", replace_existing=True)
scheduler.add_job(weekly_summary, CronTrigger(day_of_week="mon", hour=7, minute=0), id="weekly_summary", replace_existing=True)
scheduler.add_job(prune_data, CronTrigger(hour=2, minute=0), id="prune_data", replace_existing=True)

if __name__ == "__main__":
    print("Starting scheduler...")
    scheduler.start()
