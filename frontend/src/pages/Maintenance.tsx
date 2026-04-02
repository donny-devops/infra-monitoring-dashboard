import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { api } from "@/lib/api/client";
import type { MaintenanceTask, Host } from "@/lib/api/types";
import { cn, statusBg } from "@/lib/utils";
import { format, parseISO } from "date-fns";
import { toast } from "sonner";
import { Plus, Sparkles, X } from "lucide-react";

const schema = z.object({
  title: z.string().min(1),
  host_id: z.coerce.number().optional(),
  task_type: z.string().default("custom"),
  priority: z.string().default("normal"),
  scheduled_at: z.string().min(1),
  assigned_to: z.string().optional(),
  description: z.string().optional(),
});

type FormData = z.infer<typeof schema>;

const TYPES = ["custom", "patch", "backup", "restart", "inspection"];
const PRIORITIES = ["low", "normal", "high", "critical"];

export default function Maintenance() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);

  const { data: tasks } = useQuery<MaintenanceTask[]>({
    queryKey: ["maintenance"],
    queryFn: () => api.get<MaintenanceTask[]>("/maintenance"),
    refetchInterval: 60_000,
  });

  const { data: hosts } = useQuery<Host[]>({
    queryKey: ["hosts"],
    queryFn: () => api.get<Host[]>("/hosts"),
  });

  const { register, handleSubmit, reset, formState: { errors } } = useForm<FormData>({
    resolver: zodResolver(schema),
  });

  const createMutation = useMutation({
    mutationFn: (data: FormData) => api.post<MaintenanceTask>("/maintenance", data),
    onSuccess: () => {
      toast.success("Task scheduled");
      qc.invalidateQueries({ queryKey: ["maintenance"] });
      reset();
      setShowForm(false);
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: number; status: string }) =>
      api.patch(`/maintenance/${id}`, { status }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["maintenance"] }),
    onError: (e: Error) => toast.error(e.message),
  });

  const suggestMutation = useMutation({
    mutationFn: (hostId: number) => api.post("/maintenance/suggest", { host_id: hostId }),
    onSuccess: () => {
      toast.success("AI maintenance suggestions triggered — check Insights");
    },
    onError: (e: Error) => toast.error(e.message),
  });

  const scheduled = tasks?.filter((t) => t.status === "scheduled").length ?? 0;
  const overdue = tasks?.filter((t) => t.status === "overdue").length ?? 0;
  const done = tasks?.filter((t) => t.status === "done").length ?? 0;

  return (
    <div className="space-y-5">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-lg font-semibold text-slate-100">Maintenance</h1>
          <div className="flex gap-4 mt-1 text-xs text-slate-500">
            <span>{scheduled} scheduled</span>
            {overdue > 0 && <span className="text-red-400">{overdue} overdue</span>}
            <span>{done} done this period</span>
          </div>
        </div>
        <div className="flex gap-2">
          {hosts && hosts.length > 0 && (
            <button onClick={() => suggestMutation.mutate(hosts[0].id)}
              disabled={suggestMutation.isPending}
              className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-blue-400 border border-slate-700 hover:border-blue-500/50 px-3 py-1.5 rounded-md transition-colors">
              <Sparkles className="w-3.5 h-3.5" /> AI Suggest
            </button>
          )}
          <button onClick={() => setShowForm(true)}
            className="flex items-center gap-1.5 text-sm bg-blue-600 hover:bg-blue-500 text-white px-3 py-1.5 rounded-md transition-colors">
            <Plus className="w-3.5 h-3.5" /> New Task
          </button>
        </div>
      </div>

      {showForm && (
        <div className="bg-slate-900 border border-slate-700 rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-semibold text-slate-200">Schedule Task</span>
            <button onClick={() => setShowForm(false)} className="text-slate-500 hover:text-slate-300"><X className="w-4 h-4" /></button>
          </div>
          <form onSubmit={handleSubmit((d) => createMutation.mutate(d))} className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <input {...register("title")} placeholder="Task title *"
                className="w-full bg-slate-800 border border-slate-700 rounded-md px-3 py-1.5 text-sm text-slate-300 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-blue-500" />
              {errors.title && <p className="text-xs text-red-400 mt-1">{errors.title.message}</p>}
            </div>
            <select {...register("host_id")}
              className="bg-slate-800 border border-slate-700 rounded-md px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500">
              <option value="">All hosts</option>
              {hosts?.map((h) => <option key={h.id} value={h.id}>{h.name}</option>)}
            </select>
            <input {...register("scheduled_at")} type="datetime-local"
              className="bg-slate-800 border border-slate-700 rounded-md px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500" />
            <select {...register("task_type")}
              className="bg-slate-800 border border-slate-700 rounded-md px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500">
              {TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
            </select>
            <select {...register("priority")}
              className="bg-slate-800 border border-slate-700 rounded-md px-3 py-1.5 text-sm text-slate-300 focus:outline-none focus:ring-1 focus:ring-blue-500">
              {PRIORITIES.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
            <input {...register("assigned_to")} placeholder="Assigned to"
              className="bg-slate-800 border border-slate-700 rounded-md px-3 py-1.5 text-sm text-slate-300 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-blue-500" />
            <textarea {...register("description")} placeholder="Description" rows={2}
              className="col-span-2 bg-slate-800 border border-slate-700 rounded-md px-3 py-1.5 text-sm text-slate-300 placeholder:text-slate-600 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none" />
            <div className="col-span-2 flex justify-end gap-2">
              <button type="button" onClick={() => setShowForm(false)}
                className="text-sm text-slate-500 hover:text-slate-300 px-3 py-1.5">Cancel</button>
              <button type="submit" disabled={createMutation.isPending}
                className="text-sm bg-blue-600 hover:bg-blue-500 text-white px-4 py-1.5 rounded-md disabled:opacity-50">
                Schedule
              </button>
            </div>
          </form>
        </div>
      )}

      <div className="bg-slate-900 border border-slate-800 rounded-lg overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-800 text-xs text-slate-500">
              <th className="text-left px-4 py-2.5">Title</th>
              <th className="text-left px-4 py-2.5">Host</th>
              <th className="text-left px-4 py-2.5">Type</th>
              <th className="text-left px-4 py-2.5">Priority</th>
              <th className="text-left px-4 py-2.5">Scheduled</th>
              <th className="text-left px-4 py-2.5">Status</th>
              <th className="text-left px-4 py-2.5">Actions</th>
            </tr>
          </thead>
          <tbody>
            {tasks?.map((t) => (
              <tr key={t.id} className="border-b border-slate-800/50 hover:bg-slate-800/20">
                <td className="px-4 py-2.5 text-slate-300">
                  {t.title}
                  {t.ai_suggested && <span className="ml-1.5 text-xs text-blue-400">✦ AI</span>}
                </td>
                <td className="px-4 py-2.5 text-slate-500 text-xs">{t.host_name ?? "—"}</td>
                <td className="px-4 py-2.5 text-slate-500 text-xs">{t.task_type}</td>
                <td className="px-4 py-2.5 text-slate-400 text-xs">{t.priority}</td>
                <td className="px-4 py-2.5 text-slate-400 text-xs">
                  {format(parseISO(t.scheduled_at), "MMM d, HH:mm")}
                </td>
                <td className="px-4 py-2.5">
                  <span className={cn("text-xs px-1.5 py-0.5 rounded border", statusBg(t.status))}>{t.status}</span>
                </td>
                <td className="px-4 py-2.5">
                  <div className="flex gap-2 text-xs">
                    {t.status === "scheduled" && (
                      <button onClick={() => updateMutation.mutate({ id: t.id, status: "in_progress" })}
                        className="text-slate-500 hover:text-purple-400 transition-colors">Start</button>
                    )}
                    {t.status === "in_progress" && (
                      <button onClick={() => updateMutation.mutate({ id: t.id, status: "done" })}
                        className="text-slate-500 hover:text-green-400 transition-colors">Done</button>
                    )}
                    {t.status !== "done" && t.status !== "cancelled" && (
                      <button onClick={() => updateMutation.mutate({ id: t.id, status: "cancelled" })}
                        className="text-slate-500 hover:text-red-400 transition-colors">Cancel</button>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {tasks?.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-slate-600 text-sm">No tasks scheduled</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
