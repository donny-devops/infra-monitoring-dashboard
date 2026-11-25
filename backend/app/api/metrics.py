import time
from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, request, abort
from app.extensions import db, redis_client
from app.models.host import Host
from app.models.metric_snapshot import MetricSnapshot
from app.services.metric_service import get_latest_cached, get_time_series
from app.utils.sse import sse_stream
import json

metrics_bp = Blueprint("metrics", __name__, url_prefix="/api/v1")

VALID_METRICS = {
    "cpu_pct", "mem_pct", "disk_pct", "net_rx_kbps", "net_tx_kbps", "load_1m", "load_5m", "load_15m"
}
MAX_WINDOW = timedelta(days=7)


def _aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _window():
    now = datetime.now(timezone.utc)
    raw_from = request.args.get("from")
    raw_to = request.args.get("to")
    try:
        from_dt = _aware(datetime.fromisoformat(raw_from)) if raw_from else now - timedelta(hours=1)
        to_dt = _aware(datetime.fromisoformat(raw_to)) if raw_to else now
    except ValueError:
        abort(400, description="Invalid from/to datetime format")
    if to_dt <= from_dt:
        abort(400, description="to must be after from")
    if to_dt - from_dt > MAX_WINDOW:
        abort(400, description="time window cannot exceed 7 days")
    return from_dt, to_dt


@metrics_bp.get("/hosts/<int:host_id>/metrics/latest")
def latest_metrics(host_id):
    db.get_or_404(Host, host_id)
    cached = get_latest_cached(host_id)
    if cached:
        return jsonify(cached)
    snap = MetricSnapshot.query.filter_by(host_id=host_id).order_by(MetricSnapshot.collected_at.desc()).first()
    if not snap:
        return jsonify(None)
    return jsonify(snap.to_dict())


@metrics_bp.get("/hosts/<int:host_id>/metrics")
def host_metrics(host_id):
    db.get_or_404(Host, host_id)
    metric = request.args.get("metric", "cpu_pct")
    if metric not in VALID_METRICS:
        abort(400, description=f"Invalid metric. Choose from: {', '.join(sorted(VALID_METRICS))}")

    from_dt, to_dt = _window()
    span = (to_dt - from_dt).total_seconds()
    resolution = 1 if span <= 3600 else 5 if span <= 21600 else 60

    series = get_time_series(host_id, metric, from_dt, to_dt, resolution)
    return jsonify({"metric": metric, "resolution_minutes": resolution, "data": series})


@metrics_bp.get("/hosts/<int:host_id>/metrics/stream")
def host_metrics_stream(host_id):
    db.get_or_404(Host, host_id)

    def generate():
        pubsub = redis_client.pubsub()
        pubsub.subscribe(f"metrics:live:{host_id}")
        try:
            deadline = time.time() + 300  # 5-min max
            while time.time() < deadline:
                msg = pubsub.get_message(timeout=15)
                if msg and msg["type"] == "message":
                    try:
                        yield json.loads(msg["data"])
                    except (TypeError, ValueError):
                        continue
                else:
                    yield None
        finally:
            pubsub.unsubscribe()
            pubsub.close()

    return sse_stream(generate)


@metrics_bp.get("/metrics/stream")
def all_metrics_stream():
    def generate():
        pubsub = redis_client.pubsub()
        pubsub.psubscribe("metrics:live:*")
        try:
            deadline = time.time() + 300
            while time.time() < deadline:
                msg = pubsub.get_message(timeout=15)
                if msg and msg["type"] == "pmessage":
                    try:
                        yield json.loads(msg["data"])
                    except (TypeError, ValueError):
                        continue
                else:
                    yield None
        finally:
            pubsub.punsubscribe()
            pubsub.close()

    return sse_stream(generate)
