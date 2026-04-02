from flask import Blueprint, jsonify
from sqlalchemy import text
from app.extensions import db, redis_client
from app.models.host import Host
from app.models.alert import Alert
from app.models.maintenance_task import MaintenanceTask

health_bp = Blueprint("health", __name__, url_prefix="/api/v1")


@health_bp.get("/health")
def liveness():
    return jsonify({"status": "ok"}), 200


@health_bp.get("/ready")
def readiness():
    errors = []
    try:
        db.session.execute(text("SELECT 1"))
    except Exception as e:
        errors.append(f"db: {e}")
    try:
        redis_client.ping()
    except Exception as e:
        errors.append(f"redis: {e}")
    if errors:
        return jsonify({"status": "degraded", "errors": errors}), 503
    return jsonify({"status": "ok"}), 200


@health_bp.get("/stats")
def stats():
    return jsonify({
        "hosts": Host.query.filter_by(is_active=True).count(),
        "alerts_firing": Alert.query.filter_by(status="firing").count(),
        "alerts_critical": Alert.query.filter_by(status="firing", severity="critical").count(),
        "tasks_due_today": MaintenanceTask.query.filter(
            MaintenanceTask.status == "scheduled",
        ).count(),
    })
