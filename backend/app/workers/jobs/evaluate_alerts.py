from app.models.host import Host
from app.services.alert_service import evaluate_rules


def run_alert_evaluation():
    hosts = Host.query.filter_by(is_active=True).all()
    for host in hosts:
        try:
            evaluate_rules(host.id)
        except Exception:
            pass
