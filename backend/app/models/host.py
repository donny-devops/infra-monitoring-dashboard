import secrets
from datetime import datetime, timezone
from app.extensions import db


class Host(db.Model):
    __tablename__ = "hosts"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hostname = db.Column(db.String(255), nullable=False, unique=True)
    environment = db.Column(db.String(50), nullable=False, default="production")
    tags = db.Column(db.JSON, nullable=False, default=dict)
    ingest_token = db.Column(db.String(64), nullable=False, unique=True, default=lambda: secrets.token_hex(32))
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    snapshots = db.relationship("MetricSnapshot", back_populates="host", lazy="dynamic", cascade="all, delete-orphan")
    alerts = db.relationship("Alert", back_populates="host", lazy="dynamic", cascade="all, delete-orphan")
    insights = db.relationship("AIInsight", back_populates="host", lazy="dynamic", cascade="all, delete-orphan")
    maintenance_tasks = db.relationship("MaintenanceTask", back_populates="host", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Host {self.id} {self.hostname}>"
