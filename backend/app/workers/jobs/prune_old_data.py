from flask import current_app
from app.services.metric_service import prune_old_snapshots


def run_prune():
    retention = current_app.config.get("METRIC_RETENTION_DAYS", 90)
    deleted = prune_old_snapshots(retention)
    return deleted
