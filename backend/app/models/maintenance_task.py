from datetime import datetime, timezone
from app.extensions import db


class MaintenanceTask(db.Model):
    __tablename__ = "maintenance_tasks"

    id = db.Column(db.Integer, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey("hosts.id", ondelete="SET NULL"), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    task_type = db.Column(db.String(50), nullable=False, default="custom")   # patch, backup, restart, inspection, custom
    status = db.Column(db.String(20), nullable=False, default="scheduled")   # scheduled, in_progress, done, overdue, cancelled
    priority = db.Column(db.String(20), nullable=False, default="normal")    # low, normal, high, critical
    scheduled_at = db.Column(db.DateTime(timezone=True), nullable=False)
    completed_at = db.Column(db.DateTime(timezone=True))
    assigned_to = db.Column(db.String(100))
    recurrence_cron = db.Column(db.String(100))
    ai_suggested = db.Column(db.Boolean, nullable=False, default=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    host = db.relationship("Host", back_populates="maintenance_tasks")
