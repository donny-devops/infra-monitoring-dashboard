import { useState } from "react";
import type { AIInsight } from "@/lib/api/types";
import { cn, severityBg } from "@/lib/utils";
import { ChevronDown, ChevronUp, Loader2, AlertTriangle } from "lucide-react";
import { formatDistanceToNow, parseISO } from "date-fns";

const TYPE_LABELS: Record<string, string> = {
  root_cause: "Root Cause",
  anomaly: "Anomaly",
  optimization: "Maintenance Suggestion",
  weekly_summary: "Weekly Summary",
  ad_hoc: "Ad-hoc Analysis",
};

export default function InsightCard({ insight }: { insight: AIInsight }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4">
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs px-1.5 py-0.5 rounded bg-slate-800 text-slate-300 border border-slate-700">
              {TYPE_LABELS[insight.insight_type] ?? insight.insight_type}
            </span>
            {insight.severity && (
              <span className={cn("text-xs px-1.5 py-0.5 rounded border", severityBg(insight.severity))}>
                {insight.severity}
              </span>
            )}
            {insight.host_name && (
              <span className="text-xs text-slate-500">{insight.host_name}</span>
            )}
          </div>
          <p className="text-sm text-slate-300 mt-1.5 truncate">{insight.prompt_summary}</p>
          <p className="text-xs text-slate-600 mt-1">
            {formatDistanceToNow(parseISO(insight.created_at), { addSuffix: true })}
          </p>
        </div>
        <button
          onClick={() => setExpanded((v) => !v)}
          className="text-slate-500 hover:text-slate-300 flex-shrink-0 mt-0.5"
          disabled={insight.status === "pending"}
        >
          {insight.status === "pending" ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : insight.status === "failed" ? (
            <AlertTriangle className="w-4 h-4 text-red-500" />
          ) : expanded ? (
            <ChevronUp className="w-4 h-4" />
          ) : (
            <ChevronDown className="w-4 h-4" />
          )}
        </button>
      </div>

      {expanded && insight.status === "done" && (
        <div className="mt-3 pt-3 border-t border-slate-800">
          <pre className="text-xs text-slate-300 whitespace-pre-wrap font-sans leading-relaxed">
            {insight.content}
          </pre>
          {insight.recommendations.length > 0 && (
            <div className="mt-3">
              <p className="text-xs font-semibold text-slate-400 mb-1.5">Recommended Actions</p>
              <ul className="space-y-1">
                {insight.recommendations.map((rec, i) => (
                  <li key={i} className="flex gap-2 text-xs text-slate-300">
                    <span className="text-blue-400 flex-shrink-0">{i + 1}.</span>
                    {rec}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {insight.prompt_tokens && (
            <p className="text-xs text-slate-600 mt-2">
              {insight.prompt_tokens + (insight.completion_tokens ?? 0)} tokens · {insight.model}
            </p>
          )}
        </div>
      )}

      {expanded && insight.status === "failed" && (
        <div className="mt-3 pt-3 border-t border-slate-800">
          <p className="text-xs text-red-400">{insight.error}</p>
        </div>
      )}
    </div>
  );
}
