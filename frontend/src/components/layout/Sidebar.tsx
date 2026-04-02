import { Link, useLocation } from "wouter";
import { LayoutDashboard, Bell, Lightbulb, Wrench, Activity } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV = [
  { to: "/",           label: "Dashboard",   icon: LayoutDashboard },
  { to: "/alerts",     label: "Alerts",      icon: Bell },
  { to: "/insights",   label: "AI Insights", icon: Lightbulb },
  { to: "/maintenance",label: "Maintenance", icon: Wrench },
];

export default function Sidebar() {
  const [location] = useLocation();

  return (
    <aside className="w-56 bg-slate-900 border-r border-slate-800 flex flex-col">
      <div className="flex items-center gap-2 px-4 h-14 border-b border-slate-800">
        <Activity className="w-5 h-5 text-blue-400" />
        <span className="font-semibold text-slate-100 text-sm">Infra Monitor</span>
      </div>
      <nav className="flex-1 py-3 px-2 space-y-0.5">
        {NAV.map(({ to, label, icon: Icon }) => (
          <Link key={to} href={to}>
            <a className={cn(
              "flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
              location === to
                ? "bg-blue-600/20 text-blue-400"
                : "text-slate-400 hover:text-slate-200 hover:bg-slate-800"
            )}>
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
            </a>
          </Link>
        ))}
      </nav>
    </aside>
  );
}
