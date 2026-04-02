from datetime import datetime, timezone
from app.extensions import db


class AIInsight(db.Model):
    __tablename__ = "ai_insights"
    __table_args__ = (
        db.Index("ix_ai_insights_host_type_created", "host_id", "insight_type", "created_at"),
    )

    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey("hosts.id", ondelete="SET NULL"), nullable=True)
    alert_id = db.Column(db.Integer, nullable=True)
    insight_type = db.Column(db.String(50), nullable=False)  # anomaly, root_cause, optimization, weekly_summary, ad_hoc
    status = db.Column(db.String(20), nullable=False, default="pending")  # pending, done, failed
    prompt_summary = db.Column(db.Text)
    content = db.Column(db.Text)
    severity = db.Column(db.String(20))
    recommendations = db.Column(db.JSON, default=list)
    prompt_tokens = db.Column(db.Integer)
    completion_tokens = db.Column(db.Integer)
    model = db.Column(db.String(50), nullable=False, default="claude-sonnet-4-6")
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime(timezone=True))
    error = db.Column(db.Text)

    host = db.relationship("Host", back_populates="insights")

    def complete(self, content, recommendations=None, severity=None, usage=None):
        self.status = "done"
        self.content = content
        self.recommendations = recommendations or []
        self.severity = severity
        self.completed_at = datetime.now(timezone.utc)
        if usage:
            self.prompt_tokens = usage.input_tokens
            self.completion_tokens = usage.output_tokens

    def fail(self, error):
        self.status = "failed"
        self.error = str(error)
        self.completed_at = datetime.now(timezone.utc)
