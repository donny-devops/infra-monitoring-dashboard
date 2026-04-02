import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { Alert } from "@/lib/api/types";
import { cn, severityBg, statusBg } from "@/lib/utils";
import { formatDistanceToNow, parseISO } from "date-fns";
import { toast } from "sonner";
import { Sparkles } from "lucide-react";

const STATUSES = ["", "firing", "acknowledged", "resolved"];
const SEVERITIES = ["", "critical", "warning", "info"];

export default function Alerts() {
  const qc = useQueryClient();
  const [status, setStatus] = useState("");
  const [severity, setSeverity] = useState("");

  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (severity) params.set("severity", severity);

  const { data: alerts } = useQuery<Alert[]>({
    queryKey: ["alerts", status, severity],
    queryFn: () => api.get<Alert[]>(`/alerts?${params}`),
    refetchInterval: 15_000,
  });

  const ackMutation = useMutation({
    mutationFn: (id: number) => api.post(`/alerts/${id}/acknowledge`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
    onError: (e: Error) => toast.error(e.message),
  });

  const resolveMutation = useMutation({
    mutationFn: (id: number) => api.post(`/alerts/${id}/resolve`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts"] }),
    onError: (e: Error) => toast.error(e.message),
  });

  const analyzeMutation = useMutation({
    mutationFn: (id: number) => api.post(`/alerts/${id}/analyze`),
    onSuccess: () => {
      toast.success("AI analysis triggered");
      qc.invalidateQueries({ queryKey: ["insights"] });
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">Alerts</h1>
        <p className="text-sm text-slate-500">{alerts?.length ?? "—"} alerts</p>
      </div>

      <div className="flex gap-3 flex-wrap">
        <select value={status} onChange={(e) => setStatus(e.target.value)}
          className="bg-slate-900 border border-slate-800 text-slate-300 text-sm rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500">
          {STATUSES.map((s) => <option key={s} value={s}>{s || "All statuses"}</option>)}
        </select>
        <select value={severity} onChange={(e) => setSeverity(e.target.value)}
          className="bg-slate-900 border border-slate-800 text-slate-300 text-sm rounded-md px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-blue-500">
          {SEVERITIES.map((s) => <option key={s} value={s}>{s || "All severities"}</option>)}
        </select>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-xs text-slate-500">
              <th className="text-left px-4 py-2.5">Severity</th>
              <th className="text-left px-4 py-2.5">Host</th>
              <th className="text-left px-4 py-2.5">Metric</th>
              <th className="text-left px-4 py-2.5">Value</th>
              <th className="text-left px-4 py-2.5">Status</th>
              <th className="text-left px-4 py-2.5">Fired</th>
              <th className="text-left px-4 py-2.5">Actions</th>
            </tr>
          </thead>
          <tbody>
            {alerts?.map((a) => (
              <tr key={a.id} className="border-b border-slate-800/50 hover:bg-slate-800/20">
                <td className="px-4 py-2.5">
                  <span className={cn("text-xs px-1.5 py-0.5 rounded border", severityBg(a.severity))}>{a.severity}</span>
                </td>
                <td className="px-4 py-2.5 text-slate-300">{a.host_name ?? `Host ${a.host_id}`}</td>
                <td className="px-4 py-2.5 font-mono text-xs text-slate-400">{a.metric_name}</td>
                <td className="px-4 py-2.5 text-slate-300">{a.metric_value?.toFixed(1)}</td>
                <td className="px-4 py-2.5">
                  <span className={cn("text-xs px-1.5 py-0.5 rounded border", statusBg(a.status))}>{a.status}</span>
                </td>
                <td className="px-4 py-2.5 text-slate-500 text-xs">
                  {formatDistanceToNow(parseISO(a.fired_at), { addSuffix: true })}
                </td>
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-2">
                    {a.status === "firing" && (
                      <button onClick={() => ackMutation.mutate(a.id)}
                        className="text-xs text-slate-500 hover:text-yellow-400 transition-colors">Ack</button>
                    )}
                    {a.status !== "resolved" && (
                      <button onClick={() => resolveMutation.mutate(a.id)}
                        className="text-xs text-slate-500 hover:text-green-400 transition-colors">Resolve</button>
                    )}
                    <button onClick={() => analyzeMutation.mutate(a.id)}
                      className="text-xs text-slate-500 hover:text-blue-400 transition-colors flex items-center gap-1">
                      <Sparkles className="w-3 h-3" /> AI
                    </button>
                  </div>
                </td>
              </tr>
            ))}
            {alerts?.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-600 text-sm">No alerts found</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
