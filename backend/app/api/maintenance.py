from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, request, abort
from sqlalchemy import func
from app.extensions import db
from app.models.maintenance_task import MaintenanceTask
from app.models.host import Host
from app.models.metric_snapshot import MetricSnapshot
from app.models.alert import Alert
import app.services.ai_service as ai_svc
import re

maintenance_bp = Blueprint("maintenance", __name__, url_prefix="/api/v1/maintenance")

STATUSES = {"scheduled", "in_progress", "done", "cancelled"}
PRIORITIES = {"low", "normal", "high", "urgent"}
CRON_RE = re.compile(r"^[0-9*/,\- ]{1,80}$")


def _text(value, field: str, max_len: int, required: bool = True):
    if value is None and not required:
        return None
    if not isinstance(value, str):
        abort(400, description=f"{field} must be a string")
    cleaned = value.strip()
    if required and not cleaned:
        abort(400, description=f"{field} is required")
    if len(cleaned) > max_len:
        abort(400, description=f"{field} must be at most {max_len} characters")
    return cleaned or None


def _choice(value, allowed: set[str], field: str, default: str | None = None):
    if value is None and default is not None:
        return default
    if value not in allowed:
        abort(400, description=f"{field} must be one of: {', '.join(sorted(allowed))}")
    return value


def _when(value, field: str) -> datetime:
    if not isinstance(value, str):
        abort(400, description=f"{field} must be an ISO datetime")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        abort(400, description=f"{field} must be an ISO datetime")
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _host_id(value, required: bool = False):
    if value is None:
        if required:
            abort(400, description="host_id is required")
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        abort(400, description="host_id must be a positive integer")
    return value


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
        q = q.filter_by(status=_choice(status, STATUSES, "status"))
    if raw_host := request.args.get("host_id"):
        if not raw_host.isdigit():
            abort(400, description="host_id must be a positive integer")
        q = q.filter_by(host_id=int(raw_host))
    if raw_from := request.args.get("from"):
        q = q.filter(MaintenanceTask.scheduled_at >= _when(raw_from, "from"))
    if raw_to := request.args.get("to"):
        q = q.filter(MaintenanceTask.scheduled_at <= _when(raw_to, "to"))
    tasks = q.order_by(MaintenanceTask.scheduled_at).limit(200).all()
    return jsonify([_task_dict(t) for t in tasks])


@maintenance_bp.post("")
def create_task():
    data = request.get_json(silent=True) or {}
    title = _text(data.get("title"), "title", 160)
    scheduled_at = _when(data.get("scheduled_at"), "scheduled_at")
    task_type = _text(data.get("task_type", "custom"), "task_type", 32)
    if not re.fullmatch(r"[a-z0-9_-]+", task_type or ""):
        abort(400, description="task_type must be a short token")
    cron = _text(data.get("recurrence_cron"), "recurrence_cron", 80, required=False)
    if cron and not CRON_RE.fullmatch(cron):
        abort(400, description="recurrence_cron contains unsupported characters")
    task = MaintenanceTask(
        host_id=_host_id(data.get("host_id")),
        title=title,
        description=_text(data.get("description"), "description", 4000, required=False),
        task_type=task_type,
        priority=_choice(data.get("priority", "normal"), PRIORITIES, "priority"),
        scheduled_at=scheduled_at,
        assigned_to=_text(data.get("assigned_to"), "assigned_to", 80, required=False),
        recurrence_cron=cron,
        notes=_text(data.get("notes"), "notes", 4000, required=False),
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
    if "title" in data:
        task.title = _text(data["title"], "title", 160)
    if "description" in data:
        task.description = _text(data["description"], "description", 4000, required=False)
    if "status" in data:
        task.status = _choice(data["status"], STATUSES, "status")
    if "priority" in data:
        task.priority = _choice(data["priority"], PRIORITIES, "priority")
    if "assigned_to" in data:
        task.assigned_to = _text(data["assigned_to"], "assigned_to", 80, required=False)
    if "notes" in data:
        task.notes = _text(data["notes"], "notes", 4000, required=False)
    if "recurrence_cron" in data:
        cron = _text(data["recurrence_cron"], "recurrence_cron", 80, required=False)
        if cron and not CRON_RE.fullmatch(cron):
            abort(400, description="recurrence_cron contains unsupported characters")
        task.recurrence_cron = cron
    if task.status == "done" and not task.completed_at:
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
    host = db.get_or_404(Host, _host_id(data.get("host_id"), required=True))

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
    for row in rows:
        day = days[int(row.dow) % 7]
        load_profile.setdefault(day, {})[int(row.hour)] = round(float(row.avg_cpu), 1) if row.avg_cpu else 0.0

    existing = [_task_dict(task) for task in MaintenanceTask.query.filter(
        MaintenanceTask.host_id == host.id,
        MaintenanceTask.scheduled_at >= datetime.now(timezone.utc),
        MaintenanceTask.status == "scheduled",
    ).all()]

    alert_history = {}
    for severity in ("info", "warning", "critical"):
        alert_history[severity] = Alert.query.filter(
            Alert.host_id == host.id,
            Alert.fired_at >= since_4w,
            Alert.severity == severity,
        ).count()

    insight = ai_svc.suggest_maintenance(host, load_profile, existing, alert_history)
    return jsonify({"insight_id": insight.id, "status": insight.status}), 202
