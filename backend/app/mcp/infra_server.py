import json
from typing import Dict, Any
from app.services.security_service import (
    trigger_pagerduty_incident,
    generate_wazuh_rules_xml,
    parse_nmap_scan_output,
    query_threat_intelligence
)

MCP_TOOLS = [
    {
        "name": "query_infrastructure_status",
        "description": "Query cluster or host health status and metrics",
        "parameters": {
            "type": "object",
            "properties": {
                "cluster_id": {"type": "string", "description": "Cluster identifier"}
            }
        }
    },
    {
        "name": "trigger_pagerduty_alert",
        "description": "Trigger a PagerDuty incident for infrastructure anomaly",
        "parameters": {
            "type": "object",
            "properties": {
                "summary": {"type": "string", "description": "Alert summary"},
                "severity": {"type": "string", "enum": ["critical", "error", "warning", "info"]}
            },
            "required": ["summary"]
        }
    },
    {
        "name": "audit_network_ports",
        "description": "Parse raw Nmap scan output to audit open network ports and database exposures",
        "parameters": {
            "type": "object",
            "properties": {
                "nmap_output": {"type": "string", "description": "Raw output from Nmap scan"}
            },
            "required": ["nmap_output"]
        }
    },
    {
        "name": "query_threat_intel",
        "description": "Enrich an IP or hostname with threat intelligence from VirusTotal, Shodan, and GreyNoise",
        "parameters": {
            "type": "object",
            "properties": {
                "indicator": {"type": "string", "description": "IP or domain"}
            },
            "required": ["indicator"]
        }
    }
]

def handle_mcp_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "query_infrastructure_status":
        cluster_id = arguments.get("cluster_id", "default")
        return {
            "cluster_id": cluster_id,
            "status": "HEALTHY",
            "hosts_online": 6,
            "active_alerts": 0,
            "cpu_avg_percent": 34.2
        }
    elif tool_name == "trigger_pagerduty_alert":
        summary = arguments.get("summary", "Infrastructure Alert")
        severity = arguments.get("severity", "warning")
        return trigger_pagerduty_incident(summary=summary, severity=severity)
    elif tool_name == "audit_network_ports":
        nmap_out = arguments.get("nmap_output", "")
        return parse_nmap_scan_output(nmap_out)
    elif tool_name == "query_threat_intel":
        indicator = arguments.get("indicator", arguments.get("target", "127.0.0.1"))
        return query_threat_intelligence(indicator)
    return {"error": f"Unknown tool: {tool_name}"}
