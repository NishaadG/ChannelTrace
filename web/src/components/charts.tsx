import { Bar, BarChart, CartesianGrid, Cell, LabelList, Legend, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export const C = { accent: "#1F4E8C", quiet: "#C8CDD6", bad: "#B4533C", gold: "#C9A227", ink: "#14213D", grid: "#EEF1F5", muted: "#5B6478" };
export const pctFmt = (d = 0) => (v: number) => `${(v * 100).toFixed(d)}%`;

const tooltipStyle = {
  contentStyle: { background: C.ink, border: "none", borderRadius: 6, color: "#fff", fontSize: 12, padding: "8px 10px" },
  itemStyle: { color: "#fff" }, labelStyle: { color: "#C3CDE0", marginBottom: 2 }, cursor: { fill: "rgba(31,78,140,0.06)" },
};

type Row = Record<string, string | number>;

export function Bars({ data, x, y, highlight, height = 300, horizontal = false, format = pctFmt(1), axisFormat, colors, refLine, refLabel }: {
  data: Row[]; x: string; y: string; highlight?: (r: Row, i: number) => boolean; height?: number; horizontal?: boolean;
  format?: (v: number) => string; axisFormat?: (v: number) => string; colors?: (r: Row, i: number) => string; refLine?: number; refLabel?: string;
}) {
  const isPct = format(0.5).endsWith("%");
  const axis = axisFormat ?? (isPct ? pctFmt(0) : format);
  const vmax = Math.max(...data.map((d) => Number(d[y]) || 0));
  const niceMax = isPct ? Math.min(1, Math.ceil((vmax * 1.12) / 0.05) * 0.05) : "auto";
  const color = (r: Row, i: number) => (colors ? colors(r, i) : highlight?.(r, i) ? C.accent : C.quiet);
  const longest = Math.max(...data.map((d) => String(d[x]).length));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout={horizontal ? "vertical" : "horizontal"} margin={{ top: 18, right: horizontal ? 48 : 8, left: 0, bottom: 0 }}>
        <CartesianGrid stroke={C.grid} vertical={horizontal} horizontal={!horizontal} />
        {horizontal ? (
          <>
            <XAxis type="number" tickFormatter={axis} axisLine={false} tickLine={false} domain={[0, niceMax]} />
            <YAxis type="category" dataKey={x} width={Math.min(200, 24 + longest * 7.2)} axisLine={false} tickLine={false} interval={0} />
          </>
        ) : (
          <>
            <XAxis dataKey={x} axisLine={{ stroke: C.grid }} tickLine={false} interval={0} />
            <YAxis tickFormatter={axis} axisLine={false} tickLine={false} width={48} domain={[0, niceMax]} />
          </>
        )}
        <Tooltip {...tooltipStyle} formatter={(v) => format(Number(v))} />
        {refLine !== undefined && (
          <ReferenceLine {...(horizontal ? { x: refLine } : { y: refLine })} stroke={C.ink} strokeDasharray="3 3"
            label={{ value: refLabel, position: "top", fill: C.muted, fontSize: 11 }} />
        )}
        <Bar dataKey={y} radius={horizontal ? [0, 4, 4, 0] : [4, 4, 0, 0]} maxBarSize={horizontal ? 22 : 64} isAnimationActive={false}>
          {data.map((r, i) => <Cell key={i} fill={color(r, i)} />)}
          <LabelList dataKey={y} position={horizontal ? "right" : "top"} formatter={(v) => format(Number(v))} style={{ fill: C.muted, fontSize: 11 }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function PairBars({ data, x, a, b, aLabel, bLabel, height = 340, format = pctFmt(0) }: {
  data: Row[]; x: string; a: string; b: string; aLabel: string; bLabel: string; height?: number; format?: (v: number) => string;
}) {
  const longest = Math.max(...data.map((d) => String(d[x]).length));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 40, left: 0, bottom: 0 }} barGap={2}>
        <CartesianGrid stroke={C.grid} horizontal={false} />
        <XAxis type="number" tickFormatter={format} axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey={x} width={Math.min(200, 24 + longest * 7.2)} axisLine={false} tickLine={false} interval={0} />
        <Tooltip {...tooltipStyle} formatter={(v) => format(Number(v))} />
        <Legend verticalAlign="bottom" height={28} iconType="square" />
        <Bar dataKey={a} name={aLabel} fill={C.quiet} radius={[0, 3, 3, 0]} maxBarSize={14} isAnimationActive={false} />
        <Bar dataKey={b} name={bLabel} fill={C.accent} radius={[0, 3, 3, 0]} maxBarSize={14} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function Heatmap({ rows, cols, value, format = pctFmt(0) }: { rows: string[]; cols: string[]; value: (r: string, c: string) => number; format?: (v: number) => string }) {
  const all = rows.flatMap((r) => cols.map((c) => value(r, c)));
  const max = Math.max(...all), min = Math.min(...all);
  const tone = (v: number) => {
    const t = max > min ? (v - min) / (max - min) : 0;
    const mix = (a: number, b: number) => Math.round(a + (b - a) * t);
    return `rgb(${mix(244, 120)}, ${mix(246, 156)}, ${mix(249, 206)})`;
  };
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[640px] border-separate border-spacing-[3px] text-sm">
        <thead>
          <tr>
            <th />
            {cols.map((c) => <th key={c} className="px-2 pb-1 text-center text-[0.72rem] font-medium text-muted">{c}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((r) => (
            <tr key={r}>
              <td className="whitespace-nowrap pr-3 text-right text-[0.8rem] text-muted">{r}</td>
              {cols.map((c) => (
                <td key={c} title={`${r} · ${c}: ${format(value(r, c))}`} className="rounded px-2 py-2.5 text-center text-[0.82rem] font-medium tabular-nums text-ink"
                  style={{ background: tone(value(r, c)) }}>{format(value(r, c))}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Dumbbell({ items, aLabel, bLabel, format = pctFmt(0) }: { items: { label: string; a: number; b: number }[]; aLabel: string; bLabel: string; format?: (v: number) => string }) {
  const max = Math.max(...items.flatMap((i) => [i.a, i.b])) * 1.1;
  const X = (v: number) => `${(v / max) * 100}%`;
  return (
    <div>
      <div className="space-y-3">
        {items.map((it) => (
          <div key={it.label} className="grid grid-cols-[110px_1fr_84px] items-center gap-3 sm:grid-cols-[140px_1fr_96px]">
            <span className="truncate text-right text-[0.8rem] text-muted">{it.label}</span>
            <div className="relative h-6">
              <div className="absolute top-1/2 h-px w-full bg-[#EEF1F5]" />
              <div className="absolute top-1/2 h-[3px] -translate-y-1/2 rounded bg-quiet" style={{ left: X(Math.min(it.a, it.b)), width: `calc(${X(Math.abs(it.b - it.a))})` }} />
              <span title={`${aLabel}: ${format(it.a)}`} className="absolute top-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-[#9AA1AE] shadow-sm" style={{ left: X(it.a) }} />
              <span title={`${bLabel}: ${format(it.b)}`} className="absolute top-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-white bg-accent shadow-sm" style={{ left: X(it.b) }} />
            </div>
            <span className="whitespace-nowrap text-[0.75rem] tabular-nums text-muted">{format(it.a)} → <b className="text-ink">{format(it.b)}</b></span>
          </div>
        ))}
      </div>
      <div className="mt-4 flex gap-5 text-[0.75rem] text-muted">
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-[#9AA1AE]" />{aLabel}</span>
        <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-full bg-accent" />{bLabel}</span>
      </div>
    </div>
  );
}
