from datetime import datetime, timezone
from app.extensions import db


class MetricSnapshot(db.Model):
    __tablename__ = "metric_snapshots"
    __table_args__ = (
        db.Index("ix_metric_snapshots_host_time", "host_id", "collected_at"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    host_id = db.Column(db.Integer, db.ForeignKey("hosts.id", ondelete="CASCADE"), nullable=False)
    collected_at = db.Column(db.DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    cpu_pct = db.Column(db.Numeric(5, 2))
    mem_pct = db.Column(db.Numeric(5, 2))
    mem_used_mb = db.Column(db.Integer)
    disk_pct = db.Column(db.Numeric(5, 2))
    disk_used_gb = db.Column(db.Numeric(10, 2))
    net_rx_kbps = db.Column(db.Numeric(12, 2))
    net_tx_kbps = db.Column(db.Numeric(12, 2))
    load_1m = db.Column(db.Numeric(6, 2))
    load_5m = db.Column(db.Numeric(6, 2))
    load_15m = db.Column(db.Numeric(6, 2))
    extra = db.Column(db.JSON, nullable=False, default=dict)

    host = db.relationship("Host", back_populates="snapshots")

    def to_dict(self):
        return {
            "id": self.id,
            "host_id": self.host_id,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "cpu_pct": float(self.cpu_pct) if self.cpu_pct is not None else None,
            "mem_pct": float(self.mem_pct) if self.mem_pct is not None else None,
            "mem_used_mb": self.mem_used_mb,
            "disk_pct": float(self.disk_pct) if self.disk_pct is not None else None,
            "disk_used_gb": float(self.disk_used_gb) if self.disk_used_gb is not None else None,
            "net_rx_kbps": float(self.net_rx_kbps) if self.net_rx_kbps is not None else None,
            "net_tx_kbps": float(self.net_tx_kbps) if self.net_tx_kbps is not None else None,
            "load_1m": float(self.load_1m) if self.load_1m is not None else None,
            "load_5m": float(self.load_5m) if self.load_5m is not None else None,
            "load_15m": float(self.load_15m) if self.load_15m is not None else None,
            "extra": self.extra,
        }
