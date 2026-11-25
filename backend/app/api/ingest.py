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
PERCENT_FIELDS = {"cpu_pct", "mem_pct", "disk_pct"}


def _auth_host() -> Host:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        abort(401, description="Bearer token required")
    token = auth.split(" ", 1)[1].strip()
    if not token:
        abort(401, description="Bearer token required")
    host = Host.query.filter_by(ingest_token=token, is_active=True).first()
    if not host:
        abort(401, description="Invalid or inactive ingest token")
    return host


def _metric(name: str, value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        abort(400, description=f"{name} must be a number")
    number = float(value)
    if number != number or number in (float("inf"), float("-inf")):
        abort(400, description=f"{name} must be a finite number")
    if number < 0:
        abort(400, description=f"{name} cannot be negative")
    if name in PERCENT_FIELDS and number > 100:
        abort(400, description=f"{name} must be between 0 and 100")
    if number > 1_000_000_000:
        abort(400, description=f"{name} is out of range")
    return number


@ingest_bp.post("")
def push_metrics():
    host = _auth_host()
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        abort(400, description="JSON object of metrics is required")

    kwargs = {}
    for key, value in data.items():
        if key in ALLOWED_FIELDS:
            kwargs[key] = _metric(key, value)
    if not kwargs:
        abort(400, description="at least one known metric field is required")

    extra = {
        key: value
        for key, value in data.items()
        if key not in ALLOWED_FIELDS and key != "collected_at"
    }
    if len(extra) > 20:
        abort(400, description="too many extra fields")

    snapshot = MetricSnapshot(host_id=host.id, extra=extra, **kwargs)
    db.session.add(snapshot)
    db.session.commit()

    cache_latest(host.id, snapshot)

    return jsonify({"id": snapshot.id, "host_id": host.id}), 201
