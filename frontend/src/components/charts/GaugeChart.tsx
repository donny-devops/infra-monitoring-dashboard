import { RadialBarChart, RadialBar, ResponsiveContainer } from "recharts";
import { gaugeColor, formatPct } from "@/lib/utils";

interface Props {
  value: number | null;
  label: string;
  size?: number;
}

export default function GaugeChart({ value, label, size = 80 }: Props) {
  const pct = value ?? 0;
  const color = gaugeColor(value);
  const data = [{ value: pct, fill: color }];

  return (
    <div className="flex flex-col items-center gap-1" style={{ width: size }}>
      <div className="relative" style={{ width: size, height: size / 2 + 8 }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            innerRadius="60%"
            outerRadius="100%"
            data={data}
            startAngle={180}
            endAngle={0}
            cx="50%"
            cy="100%"
          >
            <RadialBar dataKey="value" cornerRadius={4} background={{ fill: "#1e293b" }} />
          </RadialBarChart>
        </ResponsiveContainer>
        <div className="absolute bottom-0 left-0 right-0 flex justify-center">
          <span className="text-sm font-semibold" style={{ color }}>{formatPct(value)}</span>
        </div>
      </div>
      <span className="text-xs text-slate-500">{label}</span>
    </div>
  );
}
