from flask import Blueprint, jsonify, request, abort
from app.extensions import db
from app.models.alert import Alert, AlertRule
from app.models.metric_snapshot import MetricSnapshot
from app.models.host import Host
import app.services.ai_service as ai_svc

alerts_bp = Blueprint("alerts", __name__, url_prefix="/api/v1/alerts")
rules_bp = Blueprint("alert_rules", __name__, url_prefix="/api/v1/alert-rules")


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
        q = q.filter_by(status=status)
    if host_id := request.args.get("host_id"):
        q = q.filter_by(host_id=int(host_id))
    if severity := request.args.get("severity"):
        q = q.filter_by(severity=severity)
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
    alert.acknowledge(actor)
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


# ── Alert Rules ──────────────────────────────

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


@rules_bp.get("")
def list_rules():
    rules = AlertRule.query.order_by(AlertRule.id).all()
    return jsonify([_rule_dict(r) for r in rules])


@rules_bp.post("")
def create_rule():
    data = request.get_json(silent=True) or {}
    required = ("metric_name", "operator", "threshold")
    for f in required:
        if f not in data:
            abort(400, description=f"{f} is required")
    if data["operator"] not in ("gt", "gte", "lt", "lte"):
        abort(400, description="operator must be one of: gt, gte, lt, lte")
    rule = AlertRule(
        host_id=data.get("host_id"),
        metric_name=data["metric_name"],
        operator=data["operator"],
        threshold=data["threshold"],
        duration_secs=data.get("duration_secs", 60),
        severity=data.get("severity", "warning"),
    )
    db.session.add(rule)
    db.session.commit()
    return jsonify(_rule_dict(rule)), 201


@rules_bp.patch("/<int:rule_id>")
def update_rule(rule_id):
    rule = db.get_or_404(AlertRule, rule_id)
    data = request.get_json(silent=True) or {}
    for field in ("threshold", "duration_secs", "severity", "is_active"):
        if field in data:
            setattr(rule, field, data[field])
    db.session.commit()
    return jsonify(_rule_dict(rule))


@rules_bp.delete("/<int:rule_id>")
def delete_rule(rule_id):
    rule = db.get_or_404(AlertRule, rule_id)
    db.session.delete(rule)
    db.session.commit()
    return "", 204
