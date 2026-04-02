import json
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, text
from app.extensions import db, redis_client
from app.models.metric_snapshot import MetricSnapshot

CACHE_TTL = 60  # seconds


def cache_latest(host_id: int, snapshot: MetricSnapshot):
    key = f"metrics:latest:{host_id}"
    redis_client.setex(key, CACHE_TTL, json.dumps(snapshot.to_dict(), default=str))


def get_latest_cached(host_id: int) -> dict | None:
    key = f"metrics:latest:{host_id}"
    raw = redis_client.get(key)
    return json.loads(raw) if raw else None


def get_time_series(host_id: int, metric: str, from_dt: datetime, to_dt: datetime, resolution_minutes: int = 5) -> list[dict]:
    rows = (
        db.session.query(
            func.date_trunc(f"{'minute' if resolution_minutes < 60 else 'hour'}", MetricSnapshot.collected_at).label("bucket"),
            func.avg(getattr(MetricSnapshot, metric, None)).label("value"),
        )
        .filter(
            MetricSnapshot.host_id == host_id,
            MetricSnapshot.collected_at.between(from_dt, to_dt),
        )
        .group_by("bucket")
        .order_by("bucket")
        .all()
    )
    return [{"time": r.bucket.isoformat(), "value": float(r.value) if r.value is not None else None} for r in rows]


def compute_baseline(host_id: int, days: int = 7) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    metrics = ["cpu_pct", "mem_pct", "disk_pct", "load_1m"]
    result = {}
    for m in metrics:
        col = getattr(MetricSnapshot, m)
        row = db.session.query(
            func.avg(col).label("mean"),
            func.stddev(col).label("stddev"),
            func.percentile_cont(0.95).within_group(col).label("p95"),
        ).filter(MetricSnapshot.host_id == host_id, MetricSnapshot.collected_at >= since).one()
        result[m] = {
            "mean": float(row.mean) if row.mean else None,
            "stddev": float(row.stddev) if row.stddev else None,
            "p95": float(row.p95) if row.p95 else None,
        }
    return result


def detect_deviations(baseline: dict, current: dict, threshold_stddev: float = 2.0) -> dict:
    deviations = {}
    for metric, base in baseline.items():
        if not base["mean"] or not base["stddev"] or metric not in current:
            continue
        val = current.get(metric)
        if val is None:
            continue
        z = (val - base["mean"]) / base["stddev"] if base["stddev"] > 0 else 0
        if abs(z) >= threshold_stddev:
            deviations[metric] = {"value": val, "z_score": round(z, 2), "baseline_mean": base["mean"]}
    return deviations


def prune_old_snapshots(retention_days: int):
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    deleted = MetricSnapshot.query.filter(MetricSnapshot.collected_at < cutoff).delete()
    db.session.commit()
    return deleted
