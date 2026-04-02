from datetime import datetime, timezone, timedelta
from sqlalchemy import func
from app.extensions import db
from app.models.host import Host
from app.models.metric_snapshot import MetricSnapshot
from app.models.alert import Alert
import app.services.ai_service as ai_svc
from app.services.metric_service import compute_baseline, detect_deviations


def run_anomaly_detection():
    hosts = Host.query.filter_by(is_active=True).all()
    since_yesterday = datetime.now(timezone.utc) - timedelta(hours=24)
    for host in hosts:
        try:
            baseline = compute_baseline(host.id, days=7)
            current = {}
            for metric in ("cpu_pct", "mem_pct", "disk_pct", "load_1m"):
                col = getattr(MetricSnapshot, metric)
                row = db.session.query(func.avg(col)).filter(
                    MetricSnapshot.host_id == host.id,
                    MetricSnapshot.collected_at >= since_yesterday,
                ).scalar()
                current[metric] = float(row) if row else None
            deviations = detect_deviations(baseline, current)
            if deviations:
                ai_svc.analyze_anomaly(host, baseline, current, deviations)
        except Exception:
            pass


def run_weekly_summary():
    from app.models.maintenance_task import MaintenanceTask
    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    hosts = Host.query.filter_by(is_active=True).all()
    summaries = []
    for host in hosts:
        avg_cpu = db.session.query(func.avg(MetricSnapshot.cpu_pct)).filter(
            MetricSnapshot.host_id == host.id,
            MetricSnapshot.collected_at >= week_ago,
        ).scalar()
        p95_cpu = db.session.query(
            func.percentile_cont(0.95).within_group(MetricSnapshot.cpu_pct)
        ).filter(
            MetricSnapshot.host_id == host.id,
            MetricSnapshot.collected_at >= week_ago,
        ).scalar()
        alerts_fired = Alert.query.filter(
            Alert.host_id == host.id,
            Alert.fired_at >= week_ago,
        ).count()
        tasks_completed = MaintenanceTask.query.filter(
            MaintenanceTask.host_id == host.id,
            MaintenanceTask.completed_at >= week_ago,
            MaintenanceTask.status == "done",
        ).count()
        summaries.append({
            "name": host.name,
            "avg_cpu": round(float(avg_cpu), 1) if avg_cpu else None,
            "p95_cpu": round(float(p95_cpu), 1) if p95_cpu else None,
            "alerts_fired": alerts_fired,
            "tasks_completed": tasks_completed,
        })
    if summaries:
        ai_svc.generate_weekly_summary(week_ago, now, summaries)
