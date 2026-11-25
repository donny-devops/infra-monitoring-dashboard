from flask import Blueprint, jsonify, request, abort
from app.extensions import db
from app.models.alert import Alert, AlertRule
from app.models.metric_snapshot import MetricSnapshot
from app.models.host import Host
import app.services.ai_service as ai_svc

alerts_bp = Blueprint("alerts", __name__, url_prefix="/api/v1/alerts")
rules_bp = Blueprint("alert_rules", __name__, url_prefix="/api/v1/alert-rules")

STATUSES = {"firing", "acknowledged", "resolved"}
SEVERITIES = {"info", "warning", "critical"}
OPERATORS = {"gt", "gte", "lt", "lte"}
METRICS = {
    "cpu_pct", "mem_pct", "mem_used_mb", "disk_pct", "disk_used_gb",
    "net_rx_kbps", "net_tx_kbps", "load_1m", "load_5m", "load_15m",
}


def _int_query(name: str):
    raw = request.args.get(name)
    if raw is None:
        return None
    if not raw.isdigit():
        abort(400, description=f"{name} must be a positive integer")
    return int(raw)


def _choice(value, allowed: set[str], field: str) -> str:
    if value not in allowed:
        abort(400, description=f"{field} must be one of: {', '.join(sorted(allowed))}")
    return value


def _number(value, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        abort(400, description=f"{field} must be a number")
    number = float(value)
    if number != number or number in (float("inf"), float("-inf")):
        abort(400, description=f"{field} must be a finite number")
    return number


def _alert_dict(alert: Alert) -> dict:
    return {
        "id": alert.id,
        "host_id": alert.host_id,
        "host_name": alert.host.name if alert.host else None,
        "rule_id": alert.rule_id,
        "status": alert.status,
        "severity": alert.severity,
        "metric_name": alert.metric_name,
        "metric_value": float(alert.metric_value) if alert.metric_value is not None else None,
        "fired_at": alert.fired_at.isoformat() if alert.fired_at else None,
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
        "resolved_at": alert.resolved_at.isoformat() if alert.resolved_at else None,
        "acknowledged_by": alert.acknowledged_by,
        "ai_insight_id": alert.ai_insight_id,
    }


@alerts_bp.get("")
def list_alerts():
    q = Alert.query
    if status := request.args.get("status"):
        q = q.filter_by(status=_choice(status, STATUSES, "status"))
    if (host_id := _int_query("host_id")) is not None:
        q = q.filter_by(host_id=host_id)
    if severity := request.args.get("severity"):
        q = q.filter_by(severity=_choice(severity, SEVERITIES, "severity"))
    alerts = q.order_by(Alert.fired_at.desc()).limit(200).all()
    return jsonify([_alert_dict(a) for a in alerts])


@alerts_bp.get("/<int:alert_id>")
def get_alert(alert_id):
    alert = db.get_or_404(Alert, alert_id)
    d = _alert_dict(alert)
    if alert.insight:
        d["insight"] = {
            "id": alert.insight.id,
            "status": alert.insight.status,
            "content": alert.insight.content,
            "recommendations": alert.insight.recommendations,
            "severity": alert.insight.severity,
        }
    return jsonify(d)


@alerts_bp.post("/<int:alert_id>/acknowledge")
def acknowledge_alert(alert_id):
    alert = db.get_or_404(Alert, alert_id)
    if alert.status not in ("firing",):
        abort(409, description=f"Alert is {alert.status}, cannot acknowledge")
    actor = (request.get_json(silent=True) or {}).get("actor", "user")
    if not isinstance(actor, str) or not actor.strip() or len(actor.strip()) > 80:
        abort(400, description="actor must be 1-80 characters")
    alert.acknowledge(actor.strip())
    db.session.commit()
    return jsonify(_alert_dict(alert))


@alerts_bp.post("/<int:alert_id>/resolve")
def resolve_alert(alert_id):
    alert = db.get_or_404(Alert, alert_id)
    if alert.status == "resolved":
        abort(409, description="Alert is already resolved")
    alert.resolve()
    db.session.commit()
    return jsonify(_alert_dict(alert))


@alerts_bp.post("/<int:alert_id>/analyze")
def analyze_alert(alert_id):
    alert = db.get_or_404(Alert, alert_id)
    host = db.get_or_404(Host, alert.host_id)
    from datetime import datetime, timezone, timedelta
    since = alert.fired_at - timedelta(hours=2)
    snapshots = MetricSnapshot.query.filter(
        MetricSnapshot.host_id == host.id,
        MetricSnapshot.collected_at >= since,
    ).order_by(MetricSnapshot.collected_at).all()
    recent = [s.to_dict() for s in snapshots]
    insight = ai_svc.analyze_root_cause(alert_id, host, alert, recent)
    alert.ai_insight_id = insight.id
    db.session.commit()
    return jsonify({"insight_id": insight.id, "status": insight.status}), 202


# ── Alert Rules ─────────────────────────────

def _rule_dict(rule: AlertRule) -> dict:
    return {
        "id": rule.id,
        "host_id": rule.host_id,
        "metric_name": rule.metric_name,
        "operator": rule.operator,
        "threshold": float(rule.threshold),
        "duration_secs": rule.duration_secs,
        "severity": rule.severity,
        "is_active": rule.is_active,
        "created_at": rule.created_at.isoformat() if rule.created_at else None,
    }


def _duration(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        abort(400, description="duration_secs must be an integer")
    if not 1 <= value <= 86_400:
        abort(400, description="duration_secs must be between 1 and 86400")
    return value


@rules_bp.get("")
def list_rules():
    rules = AlertRule.query.order_by(AlertRule.id).all()
    return jsonify([_rule_dict(r) for r in rules])


@rules_bp.post("")
def create_rule():
    data = request.get_json(silent=True) or {}
    required = ("metric_name", "operator", "threshold")
    for field in required:
        if field not in data:
            abort(400, description=f"{field} is required")
    metric_name = _choice(data["metric_name"], METRICS, "metric_name")
    operator = _choice(data["operator"], OPERATORS, "operator")
    threshold = _number(data["threshold"], "threshold")
    duration_secs = _duration(data.get("duration_secs", 60))
    severity = _choice(data.get("severity", "warning"), SEVERITIES, "severity")
    host_id = data.get("host_id")
    if host_id is not None:
        if isinstance(host_id, bool) or not isinstance(host_id, int) or host_id <= 0:
            abort(400, description="host_id must be a positive integer")
    rule = AlertRule(
        host_id=host_id,
        metric_name=metric_name,
        operator=operator,
        threshold=threshold,
        duration_secs=duration_secs,
        severity=severity,
    )
    db.session.add(rule)
    db.session.commit()
    return jsonify(_rule_dict(rule)), 201


@rules_bp.patch("/<int:rule_id>")
def update_rule(rule_id):
    rule = db.get_or_404(AlertRule, rule_id)
    data = request.get_json(silent=True) or {}
    if "threshold" in data:
        rule.threshold = _number(data["threshold"], "threshold")
    if "duration_secs" in data:
        rule.duration_secs = _duration(data["duration_secs"])
    if "severity" in data:
        rule.severity = _choice(data["severity"], SEVERITIES, "severity")
    if "is_active" in data:
        if not isinstance(data["is_active"], bool):
            abort(400, description="is_active must be a boolean")
        rule.is_active = data["is_active"]
    db.session.commit()
    return jsonify(_rule_dict(rule))


@rules_bp.delete("/<int:rule_id>")
def delete_rule(rule_id):
    rule = db.get_or_404(AlertRule, rule_id)
    db.session.delete(rule)
    db.session.commit()
    return "", 204
