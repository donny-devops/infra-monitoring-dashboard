import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { AIInsight } from "@/lib/api/types";
import InsightCard from "@/components/insights/InsightCard";
import AskAIPanel from "@/components/insights/AskAIPanel";
import { useSSE } from "@/lib/sse";

const TYPES = ["", "root_cause", "anomaly", "optimization", "weekly_summary", "ad_hoc"];

export default function Insights() {
  const qc = useQueryClient();
  const [type, setType] = useState("");

  const params = new URLSearchParams();
  if (type) params.set("type", type);

  const { data: insights, isLoading } = useQuery<AIInsight[]>({
    queryKey: ["insights", type],
    queryFn: () => api.get<AIInsight[]>(`/insights?${params}`),
    staleTime: 60_000,
  });

  useSSE<AIInsight>("/insights/stream", (data) => {
    qc.setQueryData<AIInsight[]>(["insights", type], (prev) =>
      prev ? [data, ...prev.filter((i) => i.id !== data.id)] : [data]
    );
  });

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-lg font-semibold text-slate-100">AI Insights</h1>
        <p className="text-sm text-slate-500">Anomaly detection, root cause analysis, and optimizations powered by Claude</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-4">
          <div className="flex gap-2 flex-wrap">
            {TYPES.map((t) => (
              <button key={t} onClick={() => setType(t)}
                className={`text-xs px-2.5 py-1 rounded border transition-colors ${type === t ? "bg-blue-600/20 border-blue-500/40 text-blue-400" : "border-slate-700 text-slate-500 hover:text-slate-300"}`}>
                {t || "All"}
              </button>
            ))}
          </div>

          {isLoading && <p className="text-sm text-slate-600">Loading…</p>}
          {!isLoading && !insights?.length && (
            <div className="bg-slate-900 border border-slate-800 rounded-lg p-8 text-center text-slate-600 text-sm">
              No insights yet. Trigger an analysis from the Alerts page or use the Ask AI panel.
            </div>
          )}
          <div className="space-y-3">
            {insights?.map((i) => <InsightCard key={i.id} insight={i} />)}
          </div>
        </div>

        <div>
          <AskAIPanel />
        </div>
      </div>
    </div>
  );
}
