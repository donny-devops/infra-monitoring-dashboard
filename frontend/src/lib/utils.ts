import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatPct(value: number | null | undefined): string {
  if (value == null) return "—";
  return `${value.toFixed(1)}%`;
}

export function formatBytes(mb: number | null | undefined): string {
  if (mb == null) return "—";
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
  return `${mb} MB`;
}

export function severityColor(severity: string): string {
  switch (severity) {
    case "critical": return "text-red-500";
    case "warning": return "text-yellow-500";
    case "info": return "text-blue-400";
    default: return "text-slate-400";
  }
}

export function severityBg(severity: string): string {
  switch (severity) {
    case "critical": return "bg-red-500/15 text-red-400 border-red-500/30";
    case "warning": return "bg-yellow-500/15 text-yellow-400 border-yellow-500/30";
    case "info": return "bg-blue-500/15 text-blue-400 border-blue-500/30";
    default: return "bg-slate-500/15 text-slate-400 border-slate-500/30";
  }
}

export function statusBg(status: string): string {
  switch (status) {
    case "firing": return "bg-red-500/15 text-red-400 border-red-500/30";
    case "acknowledged": return "bg-yellow-500/15 text-yellow-400 border-yellow-500/30";
    case "resolved": return "bg-green-500/15 text-green-400 border-green-500/30";
    case "done": return "bg-green-500/15 text-green-400 border-green-500/30";
    case "overdue": return "bg-red-500/15 text-red-400 border-red-500/30";
    case "scheduled": return "bg-blue-500/15 text-blue-400 border-blue-500/30";
    case "in_progress": return "bg-purple-500/15 text-purple-400 border-purple-500/30";
    case "cancelled": return "bg-slate-500/15 text-slate-400 border-slate-500/30";
    default: return "bg-slate-500/15 text-slate-400 border-slate-500/30";
  }
}

export function gaugeColor(pct: number | null): string {
  if (pct == null) return "#64748b";
  if (pct >= 90) return "#ef4444";
  if (pct >= 75) return "#f59e0b";
  return "#22c55e";
}
