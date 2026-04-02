import { Link } from "wouter";
import type { Host } from "@/lib/api/types";
import GaugeChart from "@/components/charts/GaugeChart";
import { cn } from "@/lib/utils";

function envBadge(env: string) {
  const cls: Record<string, string> = {
    production: "bg-red-500/15 text-red-400 border-red-500/30",
    staging: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
    dev: "bg-blue-500/15 text-blue-400 border-blue-500/30",
  };
  return cls[env] ?? "bg-slate-500/15 text-slate-400 border-slate-500/30";
}

function healthDot(host: Host) {
  const m = host.latest_metrics;
  if (!m) return "bg-slate-500";
  const cpu = m.cpu_pct ?? 0;
  const mem = m.mem_pct ?? 0;
  if (cpu >= 90 || mem >= 90) return "bg-red-500";
  if (cpu >= 75 || mem >= 75) return "bg-yellow-500";
  return "bg-green-500";
}

export default function HostCard({ host }: { host: Host }) {
  const m = host.latest_metrics;

  return (
    <Link href={`/hosts/${host.id}`}>
      <a className="block bg-slate-900 border border-slate-800 rounded-lg p-4 hover:border-slate-700 transition-colors cursor-pointer">
        <div className="flex items-start justify-between mb-3">
          <div>
            <div className="flex items-center gap-2">
              <span className={cn("w-2 h-2 rounded-full pulse-dot flex-shrink-0", healthDot(host))} />
              <span className="text-sm font-medium text-slate-100">{host.name}</span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5 ml-4">{host.hostname}</p>
          </div>
          <span className={cn("text-xs px-1.5 py-0.5 rounded border", envBadge(host.environment))}>
            {host.environment}
          </span>
        </div>
        {m ? (
          <div className="flex justify-around mt-2">
            <GaugeChart value={m.cpu_pct} label="CPU" size={72} />
            <GaugeChart value={m.mem_pct} label="MEM" size={72} />
            <GaugeChart value={m.disk_pct} label="DISK" size={72} />
          </div>
        ) : (
          <div className="text-center text-xs text-slate-600 py-4">No metrics yet</div>
        )}
      </a>
    </Link>
  );
}
