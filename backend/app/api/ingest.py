from flask import Blueprint, request, jsonify, abort
from app.extensions import db
from app.models.host import Host
from app.models.metric_snapshot import MetricSnapshot
from app.services.metric_service import cache_latest

ingest_bp = Blueprint("ingest", __name__, url_prefix="/api/v1/ingest")

ALLOWED_FIELDS = {
    "cpu_pct", "mem_pct", "mem_used_mb", "disk_pct", "disk_used_gb",
    "net_rx_kbps", "net_tx_kbps", "load_1m", "load_5m", "load_15m",
}


def _auth_host() -> Host:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        abort(401, description="Bearer token required")
    token = auth.split(" ", 1)[1].strip()
    host = Host.query.filter_by(ingest_token=token, is_active=True).first()
    if not host:
        abort(401, description="Invalid or inactive ingest token")
    return host


@ingest_bp.post("")
def push_metrics():
    host = _auth_host()
    data = request.get_json(silent=True) or {}

    kwargs = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
    extra = {k: v for k, v in data.items() if k not in ALLOWED_FIELDS and k != "collected_at"}

    snapshot = MetricSnapshot(host_id=host.id, extra=extra, **kwargs)
    db.session.add(snapshot)
    db.session.commit()

    cache_latest(host.id, snapshot)

    return jsonify({"id": snapshot.id, "host_id": host.id}), 201
