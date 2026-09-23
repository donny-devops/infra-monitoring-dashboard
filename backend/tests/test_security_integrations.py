import unittest
import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.services.security_service import (
    trigger_pagerduty_incident,
    generate_wazuh_rules_xml,
    parse_nmap_scan_output,
    query_threat_intelligence
)
from app.mcp.infra_server import handle_mcp_call

class TestSecurityIntegrations(unittest.TestCase):

    def test_pagerduty_incident_trigger(self):
        result = trigger_pagerduty_incident(
            summary="CPU Spike on node worker-03",
            severity="critical",
            source="infra-monitor-agent",
            custom_details={"cpu_utilization": 98.4}
        )
        self.assertIn("status", result)
        self.assertIn("dedup_key", result)
        self.assertTrue(result["dedup_key"].startswith("pd-dedup-"))

    def test_wazuh_xml_generation(self):
        rules_xml = generate_wazuh_rules_xml()
        self.assertIn('<group name="infrastructure_monitor,syslog,alerts">', rules_xml)
        self.assertIn('<rule id="100301" level="12">', rules_xml)
        self.assertIn('<mitre>', rules_xml)
        self.assertIn('</group>', rules_xml)

    def test_nmap_output_parser(self):
        sample_nmap = """
Nmap scan report for prod-db-primary.internal (10.0.1.50)
Host is up (0.00042s latency).
PORT     STATE SERVICE
22/tcp   open  ssh
80/tcp   closed http
443/tcp  open  https
3306/tcp open  mysql
5432/tcp open  postgresql
6379/tcp open  redis
8080/tcp open  http-proxy
"""
        parsed = parse_nmap_scan_output(sample_nmap)
        self.assertEqual(parsed["host"], "prod-db-primary.internal (10.0.1.50)")
        self.assertGreaterEqual(len(parsed["open_ports"]), 4)
        
        exposed_services = [p["service"] for p in parsed["open_ports"] if p["risk"] == "HIGH"]
        self.assertIn("mysql", exposed_services)
        self.assertIn("postgresql", exposed_services)
        self.assertIn("redis", exposed_services)

    def test_threat_intelligence_query(self):
        intel = query_threat_intelligence("1.1.1.1")
        self.assertEqual(intel["indicator"], "1.1.1.1")
        self.assertIn("virustotal", intel)
        self.assertIn("shodan", intel)
        self.assertIn("greynoise", intel)
        self.assertEqual(intel["virustotal"]["malicious"], 0)

    def test_mcp_server_tools(self):
        mcp_res = handle_mcp_call("query_infrastructure_status", {"cluster_id": "us-east-1"})
        self.assertEqual(mcp_res["cluster_id"], "us-east-1")
        self.assertEqual(mcp_res["status"], "HEALTHY")

        pd_mcp = handle_mcp_call("trigger_pagerduty_alert", {
            "summary": "Disk failure warning",
            "severity": "high"
        })
        self.assertEqual(pd_mcp["status"], "dispatched")

        nmap_mcp = handle_mcp_call("audit_network_ports", {
            "nmap_output": "PORT 22/tcp open ssh\nPORT 6379/tcp open redis"
        })
        self.assertEqual(nmap_mcp["total_open_ports"], 2)
        self.assertEqual(nmap_mcp["high_exposure_findings"], 1)

if __name__ == "__main__":
    unittest.main()
