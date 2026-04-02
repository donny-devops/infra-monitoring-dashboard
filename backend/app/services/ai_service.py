import re
import json
from datetime import datetime, timezone
from flask import current_app
import anthropic

from app.extensions import db, redis_client
from app.models.ai_insight import AIInsight

MODEL = "claude-sonnet-4-6"
REDIS_INSIGHT_CHANNEL = "insights:completed"


def _client():
    return anthropic.Anthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])


def _publish_insight(insight_id: int):
    try:
        redis_client.publish(REDIS_INSIGHT_CHANNEL, str(insight_id))
    except Exception:
        pass


def _extract_recommendations(content: str) -> list[str]:
    lines = content.splitlines()
    recs = []
    in_section = False
    for line in lines:
        if "RECOMMENDED ACTIONS" in line.upper():
            in_section = True
            continue
        if in_section:
            stripped = line.strip()
            if stripped.startswith(("#", "##", "###")):
                break
            if re.match(r"^(\d+\.|[-*])\s+", stripped):
                recs.append(re.sub(r"^(\d+\.|[-*])\s+", "", stripped))
    return recs[:10]


def _extract_severity(content: str) -> str:
    lower = content.lower()
    if "critical" in lower:
        return "critical"
    if "warning" in lower or "warn" in lower:
        return "warning"
    return "info"


def analyze_root_cause(alert_id: int, host, alert, recent_metrics: list[dict]) -> AIInsight:
    insight = AIInsight(
        host_id=host.id,
        alert_id=alert_id,
        insight_type="root_cause",
        prompt_summary=f"Root cause analysis for {alert.metric_name} alert on {host.hostname}",
        model=MODEL,
    )
    db.session.add(insight)
    db.session.commit()

    if not current_app.config.get("AI_ANALYSIS_ENABLED"):
        insight.fail("AI analysis is disabled")
        db.session.commit()
        return insight

    metric_table = "\n".join(
        f"{m['collected_at']}  cpu={m.get('cpu_pct')}%  mem={m.get('mem_pct')}%  disk={m.get('disk_pct')}%  load={m.get('load_1m')}"
        for m in recent_metrics
    )

    prompt = f"""You are an infrastructure reliability engineer analyzing a production alert.

HOST: {host.name} ({host.hostname}) — environment: {host.environment}
ALERT: {alert.metric_name} is {alert.metric_value} (severity: {alert.severity})
FIRED AT: {alert.fired_at.isoformat()}

RECENT METRICS (last 2h, 5-min intervals):
{metric_table or "No recent metrics available"}

Provide a structured analysis with these exact sections:

## SEVERITY ASSESSMENT
Is this critical, warning, or informational given the context?

## PROBABLE ROOT CAUSE
Most likely explanation in 2-3 sentences.

## CONTRIBUTING FACTORS
Other metrics or patterns supporting this diagnosis.

## RECOMMENDED ACTIONS
Ordered list of concrete remediation steps.

## ESTIMATED IMPACT
What services or users are likely affected?"""

    try:
        response = _client().messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        insight.complete(
            content=content,
            recommendations=_extract_recommendations(content),
            severity=_extract_severity(content),
            usage=response.usage,
        )
    except Exception as e:
        insight.fail(e)

    db.session.commit()
    _publish_insight(insight.id)
    return insight


def analyze_anomaly(host, baseline_stats: dict, current_stats: dict, deviations: dict) -> AIInsight:
    insight = AIInsight(
        host_id=host.id,
        insight_type="anomaly",
        prompt_summary=f"Anomaly detection for {host.hostname}",
        model=MODEL,
    )
    db.session.add(insight)
    db.session.commit()

    if not current_app.config.get("AI_ANALYSIS_ENABLED"):
        insight.fail("AI analysis is disabled")
        db.session.commit()
        return insight

    prompt = f"""You are analyzing infrastructure metrics for subtle anomalies that have not yet triggered alerts.

HOST: {host.name} ({host.hostname}) — environment: {host.environment}

BASELINE STATS (7-day rolling):
{json.dumps(baseline_stats, indent=2)}

YESTERDAY'S STATS:
{json.dumps(current_stats, indent=2)}

DEVIATION FLAGS:
{json.dumps(deviations, indent=2)}

Explain whether these deviations are significant, what they might indicate, and whether any proactive action should be taken before an incident occurs. Keep the response concise (under 300 words). If everything looks normal, say so briefly.

## RECOMMENDED ACTIONS
List any proactive steps, or state "No action needed" if metrics are healthy."""

    try:
        response = _client().messages.create(
            model=MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        insight.complete(
            content=content,
            recommendations=_extract_recommendations(content),
            severity=_extract_severity(content),
            usage=response.usage,
        )
    except Exception as e:
        insight.fail(e)

    db.session.commit()
    _publish_insight(insight.id)
    return insight


def generate_weekly_summary(period_start: datetime, period_end: datetime, host_summaries: list[dict]) -> AIInsight:
    insight = AIInsight(
        insight_type="weekly_summary",
        prompt_summary=f"Weekly summary {period_start.date()} to {period_end.date()}",
        model=MODEL,
    )
    db.session.add(insight)
    db.session.commit()

    if not current_app.config.get("AI_ANALYSIS_ENABLED"):
        insight.fail("AI analysis is disabled")
        db.session.commit()
        return insight

    host_rows = "\n".join(
        f"  {s['name']:30} | cpu_avg={s.get('avg_cpu', 'N/A'):>6}% | p95_cpu={s.get('p95_cpu', 'N/A'):>6}% | "
        f"alerts={s.get('alerts_fired', 0):>3} | tasks_done={s.get('tasks_completed', 0):>2}"
        for s in host_summaries
    )

    prompt = f"""You are writing a weekly infrastructure health report for an engineering team.

REPORT PERIOD: {period_start.date()} to {period_end.date()}
HOSTS MONITORED: {len(host_summaries)}

PER-HOST SUMMARY:
  {'Name':30} | avg_cpu | p95_cpu | alerts | tasks_done
{host_rows}

Write a 3-4 paragraph executive summary covering:
1. Overall fleet health this week
2. Top 2-3 hosts or issues needing attention
3. Positive trends or improvements observed
4. Recommended focus areas for next week

Follow with a bulleted action list sorted by priority.

## RECOMMENDED ACTIONS
Priority-ordered action items for next week."""

    try:
        response = _client().messages.create(
            model=MODEL,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        insight.complete(
            content=content,
            recommendations=_extract_recommendations(content),
            severity=_extract_severity(content),
            usage=response.usage,
        )
    except Exception as e:
        insight.fail(e)

    db.session.commit()
    _publish_insight(insight.id)
    return insight


def suggest_maintenance(host, load_profile: dict, existing_tasks: list[dict], alert_history: dict) -> AIInsight:
    insight = AIInsight(
        host_id=host.id,
        insight_type="optimization",
        prompt_summary=f"Maintenance window suggestions for {host.hostname}",
        model=MODEL,
    )
    db.session.add(insight)
    db.session.commit()

    if not current_app.config.get("AI_ANALYSIS_ENABLED"):
        insight.fail("AI analysis is disabled")
        db.session.commit()
        return insight

    prompt = f"""You are recommending optimal maintenance windows for a production host.

HOST: {host.name} ({host.hostname}) — environment: {host.environment}

UPCOMING SCHEDULED TASKS:
{json.dumps(existing_tasks, indent=2) if existing_tasks else "None"}

AVERAGE HOURLY CPU % (last 4 weeks, format: day_of_week: [h0, h1, ..., h23]):
{json.dumps(load_profile, indent=2)}

ALERT HISTORY (last 4 weeks by severity):
{json.dumps(alert_history, indent=2)}

Based on the load profile, identify:
1. The 3 lowest-traffic windows (day-of-week + hour range) suitable for maintenance
2. Any recurring load spikes to avoid
3. Suggested task types to prioritize given the alert history

Format as a short bulleted list with specific time windows.

## RECOMMENDED ACTIONS
Concrete maintenance tasks with suggested timing."""

    try:
        response = _client().messages.create(
            model=MODEL,
            max_tokens=700,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        insight.complete(
            content=content,
            recommendations=_extract_recommendations(content),
            severity="info",
            usage=response.usage,
        )
    except Exception as e:
        insight.fail(e)

    db.session.commit()
    _publish_insight(insight.id)
    return insight


def ad_hoc_analysis(host, question: str, recent_metrics: list[dict], recent_alerts: list[dict]) -> AIInsight:
    insight = AIInsight(
        host_id=host.id if host else None,
        insight_type="ad_hoc",
        prompt_summary=question[:200],
        model=MODEL,
    )
    db.session.add(insight)
    db.session.commit()

    if not current_app.config.get("AI_ANALYSIS_ENABLED"):
        insight.fail("AI analysis is disabled")
        db.session.commit()
        return insight

    metric_table = "\n".join(
        f"{m['collected_at']}  cpu={m.get('cpu_pct')}%  mem={m.get('mem_pct')}%  disk={m.get('disk_pct')}%"
        for m in recent_metrics[-50:]  # cap context
    ) if recent_metrics else "No metrics available"

    alert_list = "\n".join(
        f"- [{a['severity']}] {a['metric_name']} = {a['metric_value']} at {a['fired_at']}"
        for a in recent_alerts[-10:]
    ) if recent_alerts else "None"

    context = f"HOST: {host.name} ({host.hostname})\n\n" if host else ""

    prompt = f"""You are an infrastructure assistant. Answer the following question using the metric data provided. Be concise and practical.

QUESTION: {question}

{context}RECENT METRICS:
{metric_table}

RECENT ALERTS:
{alert_list}

## RECOMMENDED ACTIONS
Any concrete steps based on your answer (or "No action needed")."""

    try:
        response = _client().messages.create(
            model=MODEL,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.content[0].text
        insight.complete(
            content=content,
            recommendations=_extract_recommendations(content),
            severity=_extract_severity(content),
            usage=response.usage,
        )
    except Exception as e:
        insight.fail(e)

    db.session.commit()
    _publish_insight(insight.id)
    return insight
