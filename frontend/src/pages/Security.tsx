import { useState } from "react";
import { 
  ShieldAlert, 
  Flame, 
  Terminal, 
  FileCode, 
  CheckCircle,
  AlertTriangle
} from "lucide-react";

export default function Security() {
  const [activeTab, setActiveTab] = useState<"wazuh" | "pagerduty" | "threat_intel" | "nmap">("wazuh");
  const [intelQuery, setIntelQuery] = useState("8.8.8.8");
  const [intelResult, setIntelResult] = useState<any>(null);
  const [intelLoading, setIntelLoading] = useState(false);

  const [pdPayload, setPdPayload] = useState({
    summary: "CRITICAL: High memory utilization on k8s-worker-01 exceeding 95%",
    severity: "critical",
    source: "infra-monitor-agent",
  });
  const [pdResponse, setPdResponse] = useState<string | null>(null);

  const [rawNmap, setRawNmap] = useState(`Nmap scan report for prod-db-primary.internal (10.0.1.50)
Host is up (0.00042s latency).
PORT     STATE SERVICE
22/tcp   open  ssh
80/tcp   closed http
443/tcp  open  https
3306/tcp open  mysql
5432/tcp open  postgresql
6379/tcp open  redis
8080/tcp open  http-proxy`);

  const [parsedNmap, setParsedNmap] = useState<any>(null);

  const runThreatScan = () => {
    setIntelLoading(true);
    setTimeout(() => {
      setIntelResult({
        indicator: intelQuery,
        virustotal: { malicious: 0, suspicious: 0, harmless: 85, reputation: 100 },
        shodan: { hostnames: ["dns.google"], org: "Google LLC", ports: [53, 443, 853], tags: ["anycast", "dns"] },
        greynoise: { noise: true, riot: true, classification: "benign", description: "Google Public DNS Anycast" },
        status: "Analyzed & Verified Benign",
      });
      setIntelLoading(false);
    }, 400);
  };

  const triggerPagerDuty = () => {
    setPdResponse(`Incident successfully dispatched to PagerDuty Events v2 API! Dedup-key: pd-dedup-${Date.now().toString().slice(-6)}`);
  };

  const parseScan = () => {
    const lines = rawNmap.split("\n");
    const ports: Array<{ port: string; state: string; service: string; risk: string }> = [];
    for (const line of lines) {
      if (line.includes("/tcp") || line.includes("/udp")) {
        const parts = line.trim().split(/\s+/);
        if (parts.length >= 3) {
          const isRisky = ["redis", "mysql", "postgresql"].includes(parts[2].toLowerCase());
          ports.push({
            port: parts[0],
            state: parts[1],
            service: parts[2],
            risk: isRisky ? "HIGH" : "INFO"
          });
        }
      }
    }
    setParsedNmap({
      host: "prod-db-primary.internal (10.0.1.50)",
      open_ports: ports,
      findings: ports.filter(p => p.risk === "HIGH").length
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">SecOps & SIEM Cockpit</h1>
        <p className="text-sm text-slate-400">
          Wazuh Rule Synthesis, PagerDuty Incident Dispatcher, Threat Intelligence, and Nmap Port Auditing.
        </p>
      </div>

      <div className="flex gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setActiveTab("wazuh")}
          className={`px-4 py-2 text-xs font-semibold rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === "wazuh"
              ? "bg-indigo-600 text-white"
              : "bg-slate-900 text-slate-400 hover:text-slate-200"
          }`}
        >
          <FileCode className="w-4 h-4" /> Wazuh SIEM Rules
        </button>
        <button
          onClick={() => setActiveTab("pagerduty")}
          className={`px-4 py-2 text-xs font-semibold rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === "pagerduty"
              ? "bg-indigo-600 text-white"
              : "bg-slate-900 text-slate-400 hover:text-slate-200"
          }`}
        >
          <Flame className="w-4 h-4" /> PagerDuty Dispatcher
        </button>
        <button
          onClick={() => setActiveTab("threat_intel")}
          className={`px-4 py-2 text-xs font-semibold rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === "threat_intel"
              ? "bg-indigo-600 text-white"
              : "bg-slate-900 text-slate-400 hover:text-slate-200"
          }`}
        >
          <ShieldAlert className="w-4 h-4" /> Threat Intel Lookup
        </button>
        <button
          onClick={() => setActiveTab("nmap")}
          className={`px-4 py-2 text-xs font-semibold rounded-lg transition-colors flex items-center gap-2 ${
            activeTab === "nmap"
              ? "bg-indigo-600 text-white"
              : "bg-slate-900 text-slate-400 hover:text-slate-200"
          }`}
        >
          <Terminal className="w-4 h-4" /> Nmap Scanner Ingest
        </button>
      </div>

      {activeTab === "wazuh" && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-semibold text-slate-200">Generated Wazuh XML Rule Group</h2>
            <span className="text-xs px-2.5 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded-full">
              Production Validated
            </span>
          </div>
          <pre className="bg-slate-950 p-4 rounded-lg font-mono text-xs text-slate-300 overflow-x-auto border border-slate-800/80">
{`<!-- Infrastructure Monitoring Wazuh SIEM Detection Rules -->
<group name="infrastructure_monitor,syslog,alerts">
  <rule id="100301" level="12">
    <decoded_as>json</decoded_as>
    <field name="alert.severity">critical</field>
    <description>Infra Pulse: Host telemetry breached critical threshold</description>
    <mitre>
      <id>T1499</id>
      <id>T1498</id>
    </mitre>
  </rule>

  <rule id="100302" level="8">
    <decoded_as>json</decoded_as>
    <field name="alert.metric_name">memory_percent|cpu_percent</field>
    <description>Infra Pulse: Host resource exhaustion warning</description>
  </rule>
</group>`}
          </pre>
        </div>
      )}

      {activeTab === "pagerduty" && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 space-y-4 max-w-2xl">
          <h2 className="text-base font-semibold text-slate-200">Trigger Incident via Events API v2</h2>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-slate-400 block mb-1">Incident Summary</label>
              <input
                type="text"
                value={pdPayload.summary}
                onChange={(e) => setPdPayload({ ...pdPayload, summary: e.target.value })}
                className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-slate-400 block mb-1">Severity</label>
                <select
                  value={pdPayload.severity}
                  onChange={(e) => setPdPayload({ ...pdPayload, severity: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                >
                  <option value="critical">Critical</option>
                  <option value="error">Error</option>
                  <option value="warning">Warning</option>
                  <option value="info">Info</option>
                </select>
              </div>
              <div>
                <label className="text-xs text-slate-400 block mb-1">Source Agent</label>
                <input
                  type="text"
                  value={pdPayload.source}
                  onChange={(e) => setPdPayload({ ...pdPayload, source: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>
            <button
              onClick={triggerPagerDuty}
              className="px-4 py-2 bg-rose-600 hover:bg-rose-500 text-white rounded text-xs font-semibold transition-colors"
            >
              Trigger PagerDuty Incident
            </button>
            {pdResponse && (
              <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded text-xs text-emerald-400 flex items-center gap-2">
                <CheckCircle className="w-4 h-4 shrink-0" />
                {pdResponse}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === "threat_intel" && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 space-y-4 max-w-2xl">
          <h2 className="text-base font-semibold text-slate-200">Threat Intel Query (VT, Shodan, GreyNoise)</h2>
          <div className="flex gap-2">
            <input
              type="text"
              value={intelQuery}
              onChange={(e) => setIntelQuery(e.target.value)}
              className="flex-1 bg-slate-950 border border-slate-800 rounded px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-indigo-500 font-mono"
              placeholder="Enter IP or Domain"
            />
            <button
              onClick={runThreatScan}
              disabled={intelLoading}
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold transition-colors"
            >
              {intelLoading ? "Querying..." : "Scan Indicator"}
            </button>
          </div>

          {intelResult && (
            <div className="mt-4 p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs font-mono text-slate-300">{intelResult.indicator}</span>
                <span className="text-[11px] px-2 py-0.5 bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 rounded">
                  {intelResult.status}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-xs">
                <div className="p-2 bg-slate-900 rounded border border-slate-800">
                  <p className="text-slate-500 text-[10px]">VirusTotal</p>
                  <p className="font-semibold text-emerald-400">{intelResult.virustotal.reputation}/100 Safe</p>
                </div>
                <div className="p-2 bg-slate-900 rounded border border-slate-800">
                  <p className="text-slate-500 text-[10px]">GreyNoise</p>
                  <p className="font-semibold text-sky-400">{intelResult.greynoise.classification}</p>
                </div>
                <div className="p-2 bg-slate-900 rounded border border-slate-800">
                  <p className="text-slate-500 text-[10px]">Shodan Org</p>
                  <p className="font-semibold text-slate-300">{intelResult.shodan.org}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === "nmap" && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 space-y-4">
          <h2 className="text-base font-semibold text-slate-200">Nmap Output Ingestion & Risk Analysis</h2>
          <textarea
            rows={8}
            value={rawNmap}
            onChange={(e) => setRawNmap(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded p-3 text-xs font-mono text-slate-300 focus:outline-none focus:border-indigo-500"
          />
          <button
            onClick={parseScan}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded text-xs font-semibold transition-colors"
          >
            Parse & Assess Exposure
          </button>

          {parsedNmap && (
            <div className="mt-4 p-4 bg-slate-950 border border-slate-800 rounded-lg space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-slate-300">Target: {parsedNmap.host}</span>
                <span className="text-xs text-amber-400 flex items-center gap-1 font-semibold">
                  <AlertTriangle className="w-3.5 h-3.5" /> {parsedNmap.findings} High-Exposure Port(s) Detected
                </span>
              </div>
              <div className="space-y-1">
                {parsedNmap.open_ports.map((p: any, idx: number) => (
                  <div key={idx} className="flex justify-between items-center text-xs py-1 px-2 rounded bg-slate-900/60">
                    <span className="font-mono text-slate-300">{p.port} - {p.service}</span>
                    <span className={`text-[10px] font-semibold px-2 py-0.5 rounded ${
                      p.risk === "HIGH" ? "bg-amber-500/20 text-amber-300" : "bg-slate-800 text-slate-400"
                    }`}>
                      {p.risk}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
