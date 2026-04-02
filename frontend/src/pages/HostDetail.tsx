import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "wouter";
import { api } from "@/lib/api/client";
import type { Host, Alert, AIInsight } from "@/lib/api/types";
import GaugeChart from "@/components/charts/GaugeChart";
import TimeSeriesChart from "@/components/charts/TimeSeriesChart";
import InsightCard from "@/components/insights/InsightCard";
import AskAIPanel from "@/components/insights/AskAIPanel";
import { cn, severityBg, statusBg, formatPct } from "@/lib/utils";
import { formatDistanceToNow, parseISO } from "date-fns";
import { toast } from "sonner";
import { ArrowLeft } from "lucide-react";
import { Link } from "wouter";
import { useState } from "react";

const METRICS = [
  { key: "cpu_pct", label: "CPU", color: "#3b82f6" },
  { key: "mem_pct", label: "Memory", color: "#8b5cf6" },
  { key: "disk_pct", label: "Disk", color: "#f59e0b" },
];

const RANGES = [
  { label: "1h", hours: 1 },
  { label: "6h", hours: 6 },
  { label: "24h", hours: 24 },
  { label: "7d", hours: 168 },
];

export default function HostDetail() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [metric, setMetric] = useState("cpu_pct");
  const [range, setRange] = useState(1);

  const { data: host } = useQuery<Host>({
    queryKey: ["host", id],
    queryFn: () => api.get<Host>(`/hosts/${id}`),
  });

  const now = new Date();
  const from = new Date(now.getTime() - range * 3600 * 1000).toISOString();
  const { data: series } = useQuery({
    queryKey: ["metrics", id, metric, range],
    queryFn: () => api.get<{ data: { time: string; value: number | null }[] }>(`/hosts/${id}/metrics?metric=${metric}&from=${from}&to=${now.toISOString()}`),
    enabled: !!id,
  });

  const { data: alerts } = useQuery<Alert[]>({
    queryKey: ["alerts", "host", id],
    queryFn: () => api.get<Alert[]>(`/alerts?host_id=${id}`),
  });

  const { data: insights } = useQuery<AIInsight[]>({
    queryKey: ["insights", "host", id],
    queryFn: () => api.get<AIInsight[]>(`/insights?host_id=${id}`),
  });

  const analyzeMutation = useMutation({
    mutationFn: (alertId: number) => api.post(`/alerts/${alertId}/analyze`),
    onSuccess: () => {
      toast.success("AI root cause analysis triggered");
      qc.invalidateQueries({ queryKey: ["insights", "host", id] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const ackMutation = useMutation({
    mutationFn: (alertId: number) => api.post(`/alerts/${alertId}/acknowledge`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts", "host", id] }),
    onError: (e: Error) => toast.error(e.message),
  });

  if (!host) return <div className="text-slate-500 text-sm p-4">Loading…</div>;

  const m = host.latest_metrics;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <Link href="/">
          <a className="text-slate-500 hover:text-slate-300"><ArrowLeft className="w-4 h-4" /></a>
        </Link>
        <div>
          <h1 className="text-lg font-semibold text-slate-100">{host.name}</h1>
          <p className="text-xs text-slate-500">{host.hostname} · {host.environment}</p>
        </div>
      </div>

      {/* Current metrics */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
        <p className="text-xs text-slate-500 mb-3">Current Metrics</p>
        {m ? (
          <div className="flex gap-8 flex-wrap">
            <GaugeChart value={m.cpu_pct} label="CPU" size={88} />
            <GaugeChart value={m.mem_pct} label="Memory" size={88} />
            <GaugeChart value={m.disk_pct} label="Disk" size={88} />
            <div className="flex flex-col justify-center gap-1 text-xs text-slate-400">
              <div>Load 1m: <span className="text-slate-200">{m.load_1m ?? "—"}</span></div>
              <div>Load 5m: <span className="text-slate-200">{m.load_5m ?? "—"}</span></div>
              <div>Net RX: <span className="text-slate-200">{m.net_rx_kbps ? `${m.net_rx_kbps.toFixed(0)} kbps` : "—"}</span></div>
              <div>Net TX: <span className="text-slate-200">{m.net_tx_kbps ? `${m.net_tx_kbps.toFixed(0)} kbps` : "—"}</span></div>
            </div>
          </div>
        ) : (
          <p className="text-sm text-slate-600">No metrics yet</p>
        )}
      </div>

      {/* Time series */}
      <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
        <div className="flex items-center justify-between mb-3">
          <div className="flex gap-2">
            {METRICS.map((m) => (
              <button key={m.key} onClick={() => setMetric(m.key)}
                className={cn("text-xs px-2.5 py-1 rounded border transition-colors",
                  metric === m.key ? "bg-blue-600/20 border-blue-500/40 text-blue-400" : "border-slate-700 text-slate-500 hover:text-slate-300"
                )}>
                {m.label}
              </button>
            ))}
          </div>
          <div className="flex gap-1">
            {RANGES.map((r) => (
              <button key={r.label} onClick={() => setRange(r.hours)}
                className={cn("text-xs px-2 py-0.5 rounded transition-colors",
                  range === r.hours ? "text-blue-400" : "text-slate-600 hover:text-slate-400"
                )}>
                {r.label}
              </button>
            ))}
          </div>
        </div>
        <TimeSeriesChart
          data={series?.data ?? []}
          color={METRICS.find((m2) => m2.key === metric)?.color ?? "#3b82f6"}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Alerts */}
        <div>
          <h2 className="text-sm font-semibold text-slate-400 mb-3">Alerts</h2>
          {!alerts?.length ? (
            <p className="text-sm text-slate-600">No alerts</p>
          ) : (
            <div className="space-y-2">
              {alerts.map((a) => (
                <div key={a.id} className="bg-slate-900 border border-slate-800 rounded-lg px-4 py-3 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className={cn("text-xs px-1.5 py-0.5 rounded border flex-shrink-0", severityBg(a.severity))}>{a.severity}</span>
                    <span className="text-sm text-slate-300 truncate">{a.metric_name} = {a.metric_value?.toFixed(1)}</span>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className={cn("text-xs px-1.5 py-0.5 rounded border", statusBg(a.status))}>{a.status}</span>
                    {a.status === "firing" && (
                      <>
                        <button onClick={() => ackMutation.mutate(a.id)} className="text-xs text-slate-500 hover:text-yellow-400 transition-colors">Ack</button>
                        <button onClick={() => analyzeMutation.mutate(a.id)} className="text-xs text-slate-500 hover:text-blue-400 transition-colors">Analyze</button>
                      </>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Insights */}
        <div>
          <h2 className="text-sm font-semibold text-slate-400 mb-3">AI Insights</h2>
          <div className="space-y-2 mb-3">
            {insights?.slice(0, 5).map((i) => <InsightCard key={i.id} insight={i} />)}
            {!insights?.length && <p className="text-sm text-slate-600">No insights yet</p>}
          </div>
          <AskAIPanel defaultHostId={host.id} />
        </div>
      </div>
    </div>
  );
}
