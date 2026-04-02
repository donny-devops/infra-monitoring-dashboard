import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api/client";
import type { Host, AIInsight } from "@/lib/api/types";
import { toast } from "sonner";
import { Sparkles, Loader2 } from "lucide-react";

export default function AskAIPanel({ defaultHostId }: { defaultHostId?: number }) {
  const qc = useQueryClient();
  const [question, setQuestion] = useState("");
  const [hostId, setHostId] = useState<number | "">(defaultHostId ?? "");
  const [contextHours, setContextHours] = useState(2);

  const { data: hosts } = useQuery<Host[]>({
    queryKey: ["hosts"],
    queryFn: () => api.get<Host[]>("/hosts"),
  });

  const mutation = useMutation({
    mutationFn: () =>
      api.post<{ insight_id: number; status: string }>("/insights/analyze", {
        question,
        host_id: hostId || undefined,
        context_hours: contextHours,
      }),
    onSuccess: () => {
      toast.success("Analysis triggered — results will appear in the feed shortly");
      setQuestion("");
      setTimeout(() => qc.invalidateQueries({ queryKey: ["insights"] }), 3000);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-4 space-y-3">
      <div className="flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-blue-400" />
        <span className="text-sm font-semibold text-slate-200">Ask AI</span>
      </div>

      <select
        value={hostId}
        onChange={(e) => setHostId(e.target.value ? Number(e.target.value) : "")}
        className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500"
      >
        <option value="">All hosts</option>
        {hosts?.map((h) => (
          <option key={h.id} value={h.id}>{h.name}</option>
        ))}
      </select>

      <div className="flex items-center gap-3">
        <label className="text-xs text-slate-500 whitespace-nowrap">Context: {contextHours}h</label>
        <input
          type="range" min={1} max={24} value={contextHours}
          onChange={(e) => setContextHours(Number(e.target.value))}
          className="flex-1 accent-blue-500"
        />
      </div>

      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="e.g. Why is CPU spiking every evening? Is this normal behavior?"
        rows={3}
        className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-300 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
      />

      <button
        onClick={() => mutation.mutate()}
        disabled={!question.trim() || mutation.isPending}
        className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium py-1.5 rounded-md transition-colors"
      >
        {mutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
        Analyze
      </button>
    </div>
  );
}
