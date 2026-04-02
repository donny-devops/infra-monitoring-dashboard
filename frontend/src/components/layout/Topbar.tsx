import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { Stats } from "@/lib/api/types";
import { Bell, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

export default function Topbar() {
  const { data: stats } = useQuery<Stats>({
    queryKey: ["stats"],
    queryFn: () => api.get<Stats>("/stats"),
    refetchInterval: 30_000,
  });

  return (
    <header className="h-14 bg-slate-900 border-b border-slate-800 flex items-center justify-end px-6 gap-4">
      {stats && stats.alerts_firing > 0 && (
        <div className={cn(
          "flex items-center gap-1.5 text-xs px-2 py-1 rounded-full border",
          stats.alerts_critical > 0
            ? "bg-red-500/15 text-red-400 border-red-500/30"
            : "bg-yellow-500/15 text-yellow-400 border-yellow-500/30"
        )}>
          {stats.alerts_critical > 0
            ? <AlertTriangle className="w-3.5 h-3.5" />
            : <Bell className="w-3.5 h-3.5" />}
          {stats.alerts_firing} firing
        </div>
      )}
      <div className="text-xs text-slate-500">
        {stats ? `${stats.hosts} hosts` : "Loading…"}
      </div>
    </header>
  );
}
