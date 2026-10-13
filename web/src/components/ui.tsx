import type { ReactNode } from "react";

export function Hero({ eyebrow, title, lead, children }: { eyebrow: string; title: ReactNode; lead?: ReactNode; children?: ReactNode }) {
  return (
    <section className="relative overflow-hidden bg-ink text-white">
      <div className="pointer-events-none absolute inset-0 opacity-[0.07]"
        style={{ backgroundImage: "radial-gradient(circle at 1px 1px, #fff 1px, transparent 0)", backgroundSize: "22px 22px" }} />
      <div className="relative mx-auto max-w-6xl px-5 pb-14 pt-14 sm:px-8 sm:pt-20">
        <p className="eyebrow text-gold">{eyebrow}</p>
        <h1 className="mt-3 max-w-4xl text-4xl font-semibold leading-[1.08] !text-white sm:text-5xl">{title}</h1>
        {lead && <p className="mt-5 max-w-3xl text-[1.05rem] leading-relaxed text-mist">{lead}</p>}
        {children}
      </div>
      <div className="h-[3px] bg-gold" />
    </section>
  );
}

export function Container({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <div className={`mx-auto max-w-6xl px-5 sm:px-8 ${className}`}>{children}</div>;
}

export function SectionTitle({ code, title, children }: { code: string; title: string; children?: ReactNode }) {
  return (
    <div className="mb-5 mt-12 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p className="eyebrow text-accent">{code}</p>
        <h2 className="mt-1 text-2xl font-semibold">{title}</h2>
      </div>
      {children}
    </div>
  );
}

export function Stats({ items }: { items: { label: string; value: string; note?: string; accent?: boolean }[] }) {
  return (
    <div className="card grid grid-cols-2 overflow-hidden md:grid-flow-col md:auto-cols-fr md:grid-cols-none">
      {items.map((s, i) => (
        <div key={s.label} className={`p-5 ${i ? "border-t border-rule md:border-l md:border-t-0" : ""} ${i === 1 ? "border-l border-t-0 md:border-l" : ""}`}>
          <p className="text-[0.78rem] text-muted">{s.label}</p>
          <p className={`mt-1 font-serif text-[1.9rem] font-semibold leading-tight ${s.accent ? "text-accent" : "text-ink"}`}>{s.value}</p>
          {s.note && <p className="mt-1 text-[0.76rem] text-muted">{s.note}</p>}
        </div>
      ))}
    </div>
  );
}

export function Finding({ label = "Finding", children }: { label?: string; children: ReactNode }) {
  return (
    <div className="card my-5 border-l-[3px] border-l-accent px-5 py-4">
      <p className="eyebrow text-accent">{label}</p>
      <div className="mt-1.5 text-[0.95rem] leading-relaxed text-text">{children}</div>
    </div>
  );
}

const BADGE: Record<string, string> = {
  good: "text-good border-[#bfd5c8] bg-[#eff5f1]",
  pending: "text-gold-deep border-[#e3d2a8] bg-[#faf5e8]",
  bad: "text-bad border-[#e7c3b8] bg-[#fbf0ec]",
  info: "text-accent border-[#c3d2e8] bg-accent-soft",
  neutral: "text-muted border-rule bg-paper",
};
export function Badge({ kind = "neutral", children }: { kind?: keyof typeof BADGE; children: ReactNode }) {
  return <span className={`inline-block whitespace-nowrap rounded border px-2 py-0.5 text-[0.7rem] font-semibold tracking-wide ${BADGE[kind]}`}>{children}</span>;
}

export function Tabs<T extends string>({ tabs, value, onChange }: { tabs: { id: T; label: string }[]; value: T; onChange: (t: T) => void }) {
  return (
    <div className="mb-6 flex gap-6 overflow-x-auto border-b border-rule" role="tablist">
      {tabs.map((t) => (
        <button key={t.id} role="tab" aria-selected={value === t.id} onClick={() => onChange(t.id)}
          className={`-mb-px whitespace-nowrap border-b-2 py-3 text-sm font-medium transition-colors ${value === t.id ? "border-accent text-ink" : "border-transparent text-muted hover:text-ink"}`}>
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function ChartCard({ title, subtitle, children, className = "" }: { title: string; subtitle?: string; children: ReactNode; className?: string }) {
  return (
    <div className={`card p-5 ${className}`}>
      <h3 className="font-sans text-[0.95rem] font-semibold text-ink">{title}</h3>
      {subtitle && <p className="mt-0.5 text-[0.78rem] text-muted">{subtitle}</p>}
      <div className="mt-4">{children}</div>
    </div>
  );
}

export function Table({ head, rows, numeric = [] }: { head: string[]; rows: ReactNode[][]; numeric?: number[] }) {
  return (
    <div className="card overflow-x-auto">
      <table className="w-full min-w-[600px] border-collapse text-sm">
        <thead>
          <tr className="bg-ink-2">
            {head.map((h, i) => (
              <th key={h} className={`px-4 py-3 text-[0.7rem] font-semibold uppercase tracking-wider text-[#e4e9f2] ${numeric.includes(i) ? "text-right" : "text-left"}`}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={i} className="border-t border-rule">
              {r.map((c, j) => (
                <td key={j} className={`px-4 py-3 align-top ${numeric.includes(j) ? "text-right tabular-nums" : ""}`}>{c}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function Note({ children }: { children: ReactNode }) {
  return <p className="mt-2 text-[0.8rem] leading-relaxed text-muted">{children}</p>;
}
