import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { Host, Alert, Stats } from "@/lib/api/types";
import HostCard from "@/components/dashboard/HostCard";
import { cn, severityBg, statusBg } from "@/lib/utils";
import { Server, Bell, AlertTriangle, Wrench } from "lucide-react";
import { formatDistanceToNow, parseISO } from "date-fns";

function StatCard({ icon: Icon, label, value, accent }: { icon: React.ElementType; label: string; value: number | undefined; accent: string }) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 flex items-center gap-4">
      <div className={cn("p-2.5 rounded-lg", accent)}>
        <Icon className="w-5 h-5" />
      </div>
      <div>
        <p className="text-2xl font-bold text-slate-100">{value ?? "—"}</p>
        <p className="text-xs text-slate-500">{label}</p>
      </div>
    </div>
  );
}

export default function Dashboard() {
  const { data: hosts } = useQuery<Host[]>({ queryKey: ["hosts"], queryFn: () => api.get<Host[]>("/hosts") });
  const { data: alerts } = useQuery<Alert[]>({ queryKey: ["alerts", "firing"], queryFn: () => api.get<Alert[]>("/alerts?status=firing") });
  const { data: stats } = useQuery<Stats>({ queryKey: ["stats"], queryFn: () => api.get<Stats>("/stats") });

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">Dashboard</h1>
        <p className="text-sm text-slate-500">Fleet overview</p>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={Server}        label="Active Hosts"     value={stats?.hosts}          accent="bg-blue-500/15 text-blue-400" />
        <StatCard icon={Bell}          label="Firing Alerts"    value={stats?.alerts_firing}   accent="bg-yellow-500/15 text-yellow-400" />
        <StatCard icon={AlertTriangle} label="Critical Alerts"  value={stats?.alerts_critical} accent="bg-red-500/15 text-red-400" />
        <StatCard icon={Wrench}        label="Tasks Due Today"  value={stats?.tasks_due_today} accent="bg-purple-500/15 text-purple-400" />
      </div>

      <div>
        <h2 className="text-sm font-semibold text-slate-400 mb-3">Hosts</h2>
        {!hosts ? (
          <p className="text-sm text-slate-600">Loading hosts…</p>
        ) : hosts.length === 0 ? (
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-8 text-center text-slate-500 text-sm">
            No hosts registered yet. POST to <code className="text-slate-400">/api/v1/hosts</code> to add one.
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {hosts.map((h) => <HostCard key={h.id} host={h} />)}
          </div>
        )}
      </div>

      {alerts && alerts.length > 0 && (
        <div>
          <h2 className="text-sm font-semibold text-slate-400 mb-3">Recent Firing Alerts</h2>
          <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-800 text-xs text-slate-500">
                  <th className="text-left px-4 py-2.5">Severity</th>
                  <th className="text-left px-4 py-2.5">Host</th>
                  <th className="text-left px-4 py-2.5">Metric</th>
                  <th className="text-left px-4 py-2.5">Value</th>
                  <th className="text-left px-4 py-2.5">Fired</th>
                </tr>
              </thead>
              <tbody>
                {alerts.slice(0, 8).map((a) => (
                  <tr key={a.id} className="border-b border-slate-800/50 hover:bg-slate-800/30">
                    <td className="px-4 py-2.5">
                      <span className={cn("text-xs px-1.5 py-0.5 rounded border", severityBg(a.severity))}>
                        {a.severity}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-slate-300">{a.host_name ?? `Host ${a.host_id}`}</td>
                    <td className="px-4 py-2.5 text-slate-400 font-mono text-xs">{a.metric_name}</td>
                    <td className="px-4 py-2.5 text-slate-300">{a.metric_value?.toFixed(1)}</td>
                    <td className="px-4 py-2.5 text-slate-500 text-xs">
                      {formatDistanceToNow(parseISO(a.fired_at), { addSuffix: true })}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
