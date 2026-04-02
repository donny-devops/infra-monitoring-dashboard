import time
from datetime import datetime, timezone, timedelta
from flask import Blueprint, jsonify, request, abort
from app.extensions import db, redis_client
from app.models.ai_insight import AIInsight
from app.models.host import Host
from app.models.metric_snapshot import MetricSnapshot
from app.models.alert import Alert
import app.services.ai_service as ai_svc
from app.utils.sse import sse_stream

insights_bp = Blueprint("insights", __name__, url_prefix="/api/v1/insights")


def _insight_dict(i: AIInsight) -> dict:
    return {
        "id": i.id,
        "host_id": i.host_id,
        "host_name": i.host.name if i.host else None,
        "alert_id": i.alert_id,
        "insight_type": i.insight_type,
        "status": i.status,
        "prompt_summary": i.prompt_summary,
        "content": i.content,
        "severity": i.severity,
        "recommendations": i.recommendations,
        "prompt_tokens": i.prompt_tokens,
        "completion_tokens": i.completion_tokens,
        "model": i.model,
        "created_at": i.created_at.isoformat() if i.created_at else None,
        "completed_at": i.completed_at.isoformat() if i.completed_at else None,
        "error": i.error,
    }


@insights_bp.get("")
def list_insights():
    q = AIInsight.query
    if host_id := request.args.get("host_id"):
        q = q.filter_by(host_id=int(host_id))
    if itype := request.args.get("type"):
        q = q.filter_by(insight_type=itype)
    if status := request.args.get("status"):
        q = q.filter_by(status=status)
    items = q.order_by(AIInsight.created_at.desc()).limit(100).all()
    return jsonify([_insight_dict(i) for i in items])


@insights_bp.get("/<int:insight_id>")
def get_insight(insight_id):
    insight = db.get_or_404(AIInsight, insight_id)
    return jsonify(_insight_dict(insight))


@insights_bp.post("/analyze")
def ad_hoc_analyze():
    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()
    if not question:
        abort(400, description="question is required")

    host = None
    recent_metrics = []
    recent_alerts = []
    context_hours = min(int(data.get("context_hours", 2)), 24)

    if host_id := data.get("host_id"):
        host = db.get_or_404(Host, int(host_id))
        since = datetime.now(timezone.utc) - timedelta(hours=context_hours)
        snaps = MetricSnapshot.query.filter(
            MetricSnapshot.host_id == host.id,
            MetricSnapshot.collected_at >= since,
        ).order_by(MetricSnapshot.collected_at).all()
        recent_metrics = [s.to_dict() for s in snaps]
        alerts = Alert.query.filter(
            Alert.host_id == host.id,
            Alert.fired_at >= since,
        ).order_by(Alert.fired_at.desc()).limit(10).all()
        recent_alerts = [{"severity": a.severity, "metric_name": a.metric_name, "metric_value": str(a.metric_value), "fired_at": a.fired_at.isoformat()} for a in alerts]

    insight = ai_svc.ad_hoc_analysis(host, question, recent_metrics, recent_alerts)
    return jsonify({"insight_id": insight.id, "status": insight.status}), 202


@insights_bp.post("/weekly-summary")
def trigger_weekly_summary():
    from app.workers.jobs.run_ai_analysis import run_weekly_summary
    run_weekly_summary()
    return jsonify({"status": "triggered"}), 202


@insights_bp.get("/stream")
def insights_stream():
    def generate():
        pubsub = redis_client.pubsub()
        pubsub.subscribe(ai_svc.REDIS_INSIGHT_CHANNEL)
        try:
            deadline = time.time() + 300
            while time.time() < deadline:
                msg = pubsub.get_message(timeout=15)
                if msg and msg["type"] == "message":
                    insight_id = int(msg["data"])
                    insight = AIInsight.query.get(insight_id)
                    if insight:
                        yield _insight_dict(insight)
                else:
                    yield None
        finally:
            pubsub.unsubscribe()
            pubsub.close()

    return sse_stream(generate)
