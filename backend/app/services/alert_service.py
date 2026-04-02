from datetime import datetime, timezone
from app.extensions import db, redis_client
from app.models.alert import Alert, AlertRule
from app.models.metric_snapshot import MetricSnapshot


OPERATORS = {
    "gt":  lambda v, t: v > t,
    "gte": lambda v, t: v >= t,
    "lt":  lambda v, t: v < t,
    "lte": lambda v, t: v <= t,
}


def evaluate_rules(host_id: int):
    rules = AlertRule.query.filter(
        AlertRule.is_active == True,
        (AlertRule.host_id == host_id) | (AlertRule.host_id == None),
    ).all()

    latest = MetricSnapshot.query.filter_by(host_id=host_id).order_by(
        MetricSnapshot.collected_at.desc()
    ).first()
    if not latest:
        return

    for rule in rules:
        metric_val = getattr(latest, rule.metric_name, None)
        if metric_val is None:
            # try extra JSON
            metric_val = latest.extra.get(rule.metric_name)
        if metric_val is None:
            continue

        op = OPERATORS.get(rule.operator)
        if op and op(float(metric_val), float(rule.threshold)):
            _fire_or_update(host_id, rule, float(metric_val))
        else:
            _resolve_if_firing(host_id, rule)


def _fire_or_update(host_id: int, rule: AlertRule, value: float):
    existing = Alert.query.filter_by(host_id=host_id, rule_id=rule.id, status="firing").first()
    if existing:
        return
    alert = Alert(
        host_id=host_id,
        rule_id=rule.id,
        severity=rule.severity,
        metric_name=rule.metric_name,
        metric_value=value,
    )
    db.session.add(alert)
    db.session.commit()
    redis_client.publish(f"alerts:{host_id}", str(alert.id))
    redis_client.publish("alerts:all", str(alert.id))


def _resolve_if_firing(host_id: int, rule: AlertRule):
    alert = Alert.query.filter_by(host_id=host_id, rule_id=rule.id, status="firing").first()
    if alert:
        alert.resolve()
        db.session.commit()
        redis_client.publish(f"alerts:{host_id}", f"resolved:{alert.id}")
