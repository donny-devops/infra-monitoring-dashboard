import { Link, useLocation } from "wouter";
import { 
  LayoutDashboard, 
  Bell, 
  Sparkles, 
  Wrench, 
  ShieldCheck, 
  Activity 
} from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/alerts", label: "Alerts & Rules", icon: Bell },
  { href: "/insights", label: "AI Insights", icon: Sparkles },
  { href: "/maintenance", label: "Maintenance", icon: Wrench },
  { href: "/security", label: "Security SIEM", icon: ShieldCheck },
];

export default function Sidebar() {
  const [location] = useLocation();

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col shrink-0">
      <div className="p-4 border-b border-slate-800 flex items-center gap-3">
        <div className="p-2 bg-indigo-500/10 border border-indigo-500/30 rounded-lg text-indigo-400">
          <Activity className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-sm font-bold text-slate-100 leading-tight">Infra Pulse</h1>
          <p className="text-xs text-slate-500">Monitoring & SecOps</p>
        </div>
      </div>

      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = location === item.href;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-xs font-medium transition-colors",
                isActive
                  ? "bg-indigo-600 text-white shadow-sm"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/60"
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>

      <div className="p-3 border-t border-slate-800">
        <div className="bg-slate-950/60 rounded-lg p-3 border border-slate-800/80">
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
            <span className="text-[11px] font-medium text-slate-300">Cluster Status</span>
          </div>
          <p className="text-[10px] text-slate-500">SIEM & Telemetry Connected</p>
        </div>
      </div>
    </aside>
  );
}
