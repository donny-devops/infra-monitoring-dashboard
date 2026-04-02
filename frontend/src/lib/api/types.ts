export interface Host {
  id: number;
  name: string;
  hostname: string;
  environment: string;
  tags: Record<string, string>;
  is_active: boolean;
  ingest_token: string;
  created_at: string;
  latest_metrics?: MetricSnapshot | null;
}

export interface MetricSnapshot {
  id: number;
  host_id: number;
  collected_at: string;
  cpu_pct: number | null;
  mem_pct: number | null;
  mem_used_mb: number | null;
  disk_pct: number | null;
  disk_used_gb: number | null;
  net_rx_kbps: number | null;
  net_tx_kbps: number | null;
  load_1m: number | null;
  load_5m: number | null;
  load_15m: number | null;
  extra: Record<string, unknown>;
}

export interface TimeSeriesPoint {
  time: string;
  value: number | null;
}

export interface Alert {
  id: number;
  host_id: number;
  host_name: string | null;
  rule_id: number;
  status: "firing" | "acknowledged" | "resolved";
  severity: "info" | "warning" | "critical";
  metric_name: string;
  metric_value: number | null;
  fired_at: string;
  acknowledged_at: string | null;
  resolved_at: string | null;
  acknowledged_by: string | null;
  ai_insight_id: number | null;
  insight?: AIInsight;
}

export interface AlertRule {
  id: number;
  host_id: number | null;
  metric_name: string;
  operator: "gt" | "gte" | "lt" | "lte";
  threshold: number;
  duration_secs: number;
  severity: "info" | "warning" | "critical";
  is_active: boolean;
  created_at: string;
}

export interface AIInsight {
  id: number;
  host_id: number | null;
  host_name: string | null;
  alert_id: number | null;
  insight_type: "anomaly" | "root_cause" | "optimization" | "weekly_summary" | "ad_hoc";
  status: "pending" | "done" | "failed";
  prompt_summary: string | null;
  content: string | null;
  severity: string | null;
  recommendations: string[];
  prompt_tokens: number | null;
  completion_tokens: number | null;
  model: string;
  created_at: string;
  completed_at: string | null;
  error: string | null;
}

export interface MaintenanceTask {
  id: number;
  host_id: number | null;
  host_name: string | null;
  title: string;
  description: string | null;
  task_type: string;
  status: "scheduled" | "in_progress" | "done" | "overdue" | "cancelled";
  priority: "low" | "normal" | "high" | "critical";
  scheduled_at: string;
  completed_at: string | null;
  assigned_to: string | null;
  recurrence_cron: string | null;
  ai_suggested: boolean;
  notes: string | null;
  created_at: string;
}

export interface Stats {
  hosts: number;
  alerts_firing: number;
  alerts_critical: number;
  tasks_due_today: number;
}
