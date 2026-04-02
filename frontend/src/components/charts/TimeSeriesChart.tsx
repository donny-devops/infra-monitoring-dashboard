import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import type { TimeSeriesPoint } from "@/lib/api/types";
import { format, parseISO } from "date-fns";

interface Props {
  data: TimeSeriesPoint[];
  color?: string;
  unit?: string;
}

export default function TimeSeriesChart({ data, color = "#3b82f6", unit = "%" }: Props) {
  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis
          dataKey="time"
          tickFormatter={(v) => format(parseISO(v), "HH:mm")}
          tick={{ fill: "#64748b", fontSize: 11 }}
          tickLine={false}
          axisLine={false}
        />
        <YAxis
          tick={{ fill: "#64748b", fontSize: 11 }}
          tickLine={false}
          axisLine={false}
          tickFormatter={(v) => `${v}${unit}`}
          domain={[0, 100]}
        />
        <Tooltip
          contentStyle={{ background: "#1e293b", border: "1px solid #334155", borderRadius: 6, fontSize: 12 }}
          labelFormatter={(v) => format(parseISO(v as string), "MMM d HH:mm")}
          formatter={(v: number) => [`${v?.toFixed(1)}${unit}`, "Value"]}
        />
        <Line type="monotone" dataKey="value" stroke={color} strokeWidth={2} dot={false} />
      </LineChart>
    </ResponsiveContainer>
  );
}
