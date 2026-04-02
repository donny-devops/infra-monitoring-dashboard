from datetime import datetime, timezone
from app.extensions import db


class AlertRule(db.Model):
    __tablename__ = "alert_rules"

    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey("hosts.id", ondelete="CASCADE"), nullable=True)
    metric_name = db.Column(db.String(100), nullable=False)
    operator = db.Column(db.String(10), nullable=False)   # gt, lt, gte, lte
    threshold = db.Column(db.Numeric, nullable=False)
    duration_secs = db.Column(db.Integer, nullable=False, default=60)
    severity = db.Column(db.String(20), nullable=False, default="warning")
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    alerts = db.relationship("Alert", back_populates="rule", lazy="dynamic")


class Alert(db.Model):
    __tablename__ = "alerts"
    __table_args__ = (
        db.Index("ix_alerts_host_status_fired", "host_id", "status", "fired_at"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey("alert_rules.id"), nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="firing")
    severity = db.Column(db.String(20), nullable=False)
    metric_name = db.Column(db.String(100), nullable=False)
    metric_value = db.Column(db.Numeric)
    fired_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    acknowledged_at = db.Column(db.DateTime(timezone=True))
    resolved_at = db.Column(db.DateTime(timezone=True))
    acknowledged_by = db.Column(db.String(100))
    ai_insight_id = db.Column(db.Integer, db.ForeignKey("ai_insights.id"), nullable=True)

    rule = db.relationship("AlertRule", back_populates="alerts")
    host = db.relationship("Host", back_populates="alerts")
    insight = db.relationship("AIInsight", foreign_keys=[ai_insight_id])

    def acknowledge(self, actor="user"):
        self.status = "acknowledged"
        self.acknowledged_at = datetime.now(timezone.utc)
        self.acknowledged_by = actor

    def resolve(self):
        self.status = "resolved"
        self.resolved_at = datetime.now(timezone.utc)
