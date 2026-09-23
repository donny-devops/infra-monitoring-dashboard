from flask import Blueprint, request, jsonify
from app.services.security_service import SecurityIntegrationService

bp = Blueprint("security", __name__, url_prefix="/api/security")

@bp.route("/pagerduty/trigger", methods=["POST"])
def trigger_pagerduty():
    data = request.get_json() or {}
    payload = SecurityIntegrationService.create_pagerduty_payload(data)
    return jsonify({"success": True, "message": "PagerDuty payload formatted", "payload": payload}), 200

@bp.route("/wazuh/rules", methods=["GET"])
def get_wazuh_rules():
    rules = SecurityIntegrationService.generate_wazuh_rules()
    return jsonify({"rules_xml": rules}), 200

@bp.route("/nmap/import", methods=["POST"])
def import_nmap():
    data = request.get_json() or {}
    scan_text = data.get("scan_output", "")
    hosts = SecurityIntegrationService.parse_nmap_scan(scan_text)
    return jsonify({"success": True, "discovered_count": len(hosts), "hosts": hosts}), 200

@bp.route("/enrich", methods=["POST"])
def enrich_target():
    data = request.get_json() or {}
    target = data.get("target", "127.0.0.1")
    intel = SecurityIntegrationService.get_threat_intel_enrichment(target)
    return jsonify({"success": True, "enrichment": intel}), 200
