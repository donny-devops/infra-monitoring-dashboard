from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, request, abort
from sqlalchemy import func
from app.extensions import db
from app.models.maintenance_task import MaintenanceTask
from app.models.host import Host
from app.models.metric_snapshot import MetricSnapshot
from app.models.alert import Alert
import app.services.ai_service as ai_svc

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/api/v1/maintenance")


def _task_dict(task: MaintenanceTask) -> dict:
    return {
        "id": task.id,
        "host_id": task.host_id,
        "host_name": task.host.name if task.host else None,
        "title": task.title,
        "description": task.description,
        "task_type": task.task_type,
        "status": task.status,
        "priority": task.priority,
        "scheduled_at": task.scheduled_at.isoformat() if task.scheduled_at else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        "assigned_to": task.assigned_to,
        "recurrence_cron": task.recurrence_cron,
        "ai_suggested": task.ai_suggested,
        "notes": task.notes,
        "created_at": task.created_at.isoformat() if task.created_at else None,
    }


@maintenance_bp.get("")
def list_tasks():
    q = MaintenanceTask.query
    if status := request.args.get("status"):
        q = q.filter_by(status=status)
    if host_id := request.args.get("host_id"):
        q = q.filter_by(host_id=int(host_id))
    if from_dt := request.args.get("from"):
        q = q.filter(MaintenanceTask.scheduled_at >= datetime.fromisoformat(from_dt))
    if to_dt := request.args.get("to"):
        q = q.filter(MaintenanceTask.scheduled_at <= datetime.fromisoformat(to_dt))
    tasks = q.order_by(MaintenanceTask.scheduled_at).all()
    return jsonify([_task_dict(t) for t in tasks])


@maintenance_bp.post("")
def create_task():
    data = request.get_json(silent=True) or {}
    if not data.get("title") or not data.get("scheduled_at"):
        abort(400, description="title and scheduled_at are required")
    task = MaintenanceTask(
        host_id=data.get("host_id"),
        title=data["title"],
        description=data.get("description"),
        task_type=data.get("task_type", "custom"),
        priority=data.get("priority", "normal"),
        scheduled_at=datetime.fromisoformat(data["scheduled_at"]),
        assigned_to=data.get("assigned_to"),
        recurrence_cron=data.get("recurrence_cron"),
        notes=data.get("notes"),
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(_task_dict(task)), 201


@maintenance_bp.get("/<int:task_id>")
def get_task(task_id):
    task = db.get_or_404(MaintenanceTask, task_id)
    return jsonify(_task_dict(task))


@maintenance_bp.patch("/<int:task_id>")
def update_task(task_id):
    task = db.get_or_404(MaintenanceTask, task_id)
    data = request.get_json(silent=True) or {}
    for field in ("title", "description", "status", "priority", "assigned_to", "notes", "recurrence_cron"):
        if field in data:
            setattr(task, field, data[field])
    if data.get("status") == "done" and not task.completed_at:
        task.completed_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(_task_dict(task))


@maintenance_bp.delete("/<int:task_id>")
def cancel_task(task_id):
    task = db.get_or_404(MaintenanceTask, task_id)
    task.status = "cancelled"
    db.session.commit()
    return "", 204


@maintenance_bp.post("/suggest")
def suggest_tasks():
    data = request.get_json(silent=True) or {}
    host_id = data.get("host_id")
    if not host_id:
        abort(400, description="host_id is required")
    host = db.get_or_404(Host, int(host_id))

    since_4w = datetime.now(timezone.utc) - timedelta(weeks=4)

    # Build hourly load profile
    rows = (
        db.session.query(
            func.extract("dow", MetricSnapshot.collected_at).label("dow"),
            func.extract("hour", MetricSnapshot.collected_at).label("hour"),
            func.avg(MetricSnapshot.cpu_pct).label("avg_cpu"),
        )
        .filter(MetricSnapshot.host_id == host.id, MetricSnapshot.collected_at >= since_4w)
        .group_by("dow", "hour")
        .all()
    )
    load_profile = {}
    days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for r in rows:
        day = days[int(r.dow)]
        load_profile.setdefault(day, {})[int(r.hour)] = round(float(r.avg_cpu), 1) if r.avg_cpu else 0.0

    existing = [_task_dict(t) for t in MaintenanceTask.query.filter(
        MaintenanceTask.host_id == host.id,
        MaintenanceTask.scheduled_at >= datetime.now(timezone.utc),
        MaintenanceTask.status == "scheduled",
    ).all()]

    alert_history = {}
    for sev in ("info", "warning", "critical"):
        alert_history[sev] = Alert.query.filter(
            Alert.host_id == host.id,
            Alert.fired_at >= since_4w,
            Alert.severity == sev,
        ).count()

    insight = ai_svc.suggest_maintenance(host, load_profile, existing, alert_history)
    return jsonify({"insight_id": insight.id, "status": insight.status}), 202
