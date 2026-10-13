import Papa from "papaparse";
import { ArrowRight, FileUp } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Bars, C, Dumbbell, Heatmap, PairBars } from "../components/charts";
import { Badge, ChartCard, Container, Finding, Hero, Note, SectionTitle, Stats, Table, Tabs } from "../components/ui";
import { useData } from "../data";
import { adFacts, money, parseAds, pct, summarise, type Verdict } from "../lib/ads";
import { MODELS, attribute, buildJourneys, journeyFacts, journeyStats, shares } from "../lib/attribution";

type Tab = "ads" | "journeys";
const AD_SAMPLES = [
  { file: "facebook_ads_kaggle.csv", label: "Facebook Ads · real anonymised data (Kaggle, 1,143 ads)" },
  { file: "google_ads_synthetic_sample.csv", label: "Google Ads · synthetic sample (6 campaigns, 60 days)" },
];
const JOURNEY_SAMPLES = [{ file: "journeys_synthetic_sample.csv", label: "Customer journeys · synthetic sample (4,000 users)" }];
const VERDICT: Record<Verdict, "good" | "info" | "bad"> = { "Scale candidate": "good", "On track": "info", Expensive: "bad", "No conversions": "bad" };

function Picker({ samples, onText, hint }: { samples: { file: string; label: string }[]; onText: (t: string, name: string) => void; hint: string }) {
  const [drag, setDrag] = useState(false);
  const read = (f: File) => f.text().then((t) => onText(t, f.name));
  return (
    <div className="grid gap-4 md:grid-cols-5">
      <label onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)}
        onDrop={(e) => { e.preventDefault(); setDrag(false); if (e.dataTransfer.files[0]) read(e.dataTransfer.files[0]); }}
        className={`card flex cursor-pointer items-center gap-4 border-dashed p-5 md:col-span-3 ${drag ? "border-accent bg-accent-soft" : ""}`}>
        <FileUp className="shrink-0 text-accent" size={28} strokeWidth={1.6} />
        <div>
          <p className="text-sm font-semibold text-ink">Drop a CSV here or click to choose</p>
          <p className="mt-0.5 text-[0.8rem] text-muted">{hint}</p>
        </div>
        <input type="file" accept=".csv,.tsv,.txt" className="hidden" onChange={(e) => e.target.files?.[0] && read(e.target.files[0])} />
      </label>
      <div className="card p-5 md:col-span-2">
        <p className="text-[0.8rem] font-medium text-muted">Or try a sample</p>
        <div className="mt-2 flex flex-col gap-2">
          {samples.map((s) => (
            <button key={s.file} onClick={() => fetch(`/samples/${s.file}`).then((r) => r.text()).then((t) => onText(t, s.label))}
              className="rounded-md border border-rule px-3 py-2 text-left text-[0.82rem] text-ink transition-colors hover:border-accent hover:text-accent">{s.label}</button>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function Analyse() {
  const [tab, setTab] = useState<Tab>("ads");
  return (
    <>
      <Hero eyebrow="Analyse your data" title="Run the analysis on your own numbers"
        lead="Export a report from Google Ads, Meta Ads Manager or your analytics tool and drop it in. Everything is computed in your browser; the file is never uploaded or stored." />
      <Container className="pt-8">
        <Tabs<Tab> value={tab} onChange={setTab} tabs={[{ id: "ads", label: "Ad performance" }, { id: "journeys", label: "Customer journeys and attribution" }]} />
        {tab === "ads" ? <AdsPanel /> : <JourneyPanel />}
      </Container>
    </>
  );
}

function AdsPanel() {
  const { setDataFact } = useData();
  const [input, setInput] = useState<{ text: string; name: string }>();
  const result = useMemo(() => {
    if (!input) return undefined;
    try {
      const { rows, platform, mapping } = parseAds(input.text);
      return { platform, mapping, s: summarise(rows) };
    } catch (e) { return { error: (e as Error).message }; }
  }, [input]);
  useEffect(() => { if (result && "s" in result && result.s) setDataFact("ads", adFacts(result.s, result.platform)); }, [result]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      <Picker samples={AD_SAMPLES} onText={(text, name) => setInput({ text, name })}
        hint="Google Ads: Campaigns → Download → CSV. Meta: Ads Manager → Reports → Export. Needs campaign, cost/amount spent, clicks and conversions/results." />
      {result && "error" in result && <div className="card mt-6 border-l-[3px] border-l-bad p-5 text-sm text-bad">Could not read this file. {result.error}</div>}
      {result && "s" in result && result.s && <AdsDashboard {...result} name={input!.name} />}
    </>
  );
}

function AdsDashboard({ s, platform, mapping, name }: { s: ReturnType<typeof summarise>; platform: string; mapping: Record<string, string>; name: string }) {
  const t = s.totals;
  const share = s.campaigns.slice(0, 10).map((c) => ({ k: c.campaign, spend: c.spendShare, conv: c.convShare }));
  const cpa = s.campaigns.filter((c) => Number.isFinite(c.cpa)).slice(0, 10).sort((a, b) => a.cpa - b.cpa);
  const facts = adFacts(s, platform).split("\n").find((l) => l.startsWith("ACTION"));
  return (
    <div className="fade-in mt-8">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Badge kind="info">Detected: {platform}</Badge><Badge>{s.rows.toLocaleString()} rows</Badge><Badge>{s.campaigns.length} campaigns</Badge>
        {name.toLowerCase().includes("synthetic") && <span className="text-[0.8rem] text-muted">Synthetic sample, generated to look like a Google Ads export.</span>}
      </div>
      <Stats items={[
        { label: "Spend", value: money(t.spend), note: `${t.impressions.toLocaleString()} impressions` },
        { label: "Conversions", value: t.conversions.toLocaleString(), note: `${pct(t.cvr, 2)} of clicks` },
        { label: "Cost per acquisition", value: money(t.cpa), note: "spend ÷ conversions", accent: true },
        { label: "Click-through rate", value: pct(t.ctr, 2), note: `CPC ${money(t.cpc)}` },
        ...(s.hasRevenue ? [{ label: "Return on ad spend", value: `${t.roas.toFixed(2)}x`, note: `revenue ${money(t.revenue)}` }] : []),
      ]} />
      <Finding label="Spend with no return"><b>{pct(s.zeroShare)} of spend ({money(s.zeroSpend)})</b> went to {s.zeroCount} {s.wasteUnit} that produced no conversions. That is the first place to look for savings.</Finding>
      <div className="grid gap-5 lg:grid-cols-2">
        <ChartCard title="Share of spend vs share of conversions"><PairBars data={share} x="k" a="spend" b="conv" aLabel="Share of spend" bLabel="Share of conversions" /></ChartCard>
        <ChartCard title="Cost per acquisition by campaign" subtitle="Blue: scale candidate · red: expensive or no conversions">
          <Bars horizontal height={340} data={cpa.map((c) => ({ k: c.campaign, v: c.cpa, verdict: c.verdict }))} x="k" y="v" format={(v) => money(v)}
            refLine={t.cpa} refLabel={`account CPA ${money(t.cpa)}`}
            colors={(r) => (r.verdict === "Scale candidate" ? C.accent : r.verdict === "On track" ? C.quiet : C.bad)} />
        </ChartCard>
      </div>
      <SectionTitle code="Campaigns" title="Performance and verdict" />
      <Table head={["Campaign", "Spend", "Share", "Clicks", "Conv.", "CPA", "CVR", ...(s.hasRevenue ? ["ROAS"] : []), "Verdict"]}
        numeric={s.hasRevenue ? [1, 2, 3, 4, 5, 6, 7] : [1, 2, 3, 4, 5, 6]}
        rows={s.campaigns.map((c) => [<b className="text-ink">{c.campaign}</b>, money(c.spend), pct(c.spendShare, 0), c.clicks.toLocaleString(), c.conversions.toLocaleString(),
          money(c.cpa), pct(c.cvr), ...(s.hasRevenue ? [Number.isFinite(c.roas) ? `${c.roas.toFixed(2)}x` : "–"] : []), <Badge kind={VERDICT[c.verdict]}>{c.verdict}</Badge>])} />
      <Note>Verdicts compare each campaign's CPA with the account average: below 75% is a scale candidate, above 150% is expensive.</Note>
      {(s.age || s.gender) && (
        <>
          <SectionTitle code="Audience" title="Which segments convert cheaply" />
          <div className="grid gap-5 lg:grid-cols-2">
            {([["age", s.age], ["gender", s.gender]] as const).filter(([, d]) => d).map(([k, d]) => {
              const min = Math.min(...d!.map((x) => x.cpa));
              return <ChartCard key={k} title={`Cost per acquisition by ${k}`}><Bars data={d!.map((x) => ({ k: x.key, v: x.cpa }))} x="k" y="v" format={(v) => money(v)} highlight={(r) => r.v === min} /></ChartCard>;
            })}
          </div>
        </>
      )}
      {s.daily && (
        <>
          <SectionTitle code="Trend" title="Daily spend and conversions" />
          <div className="grid gap-5 lg:grid-cols-2">
            {(["spend", "conversions"] as const).map((k) => (
              <ChartCard key={k} title={k === "spend" ? "Spend per day" : "Conversions per day"}>
                <ResponsiveContainer width="100%" height={220}>
                  <LineChart data={s.daily} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                    <CartesianGrid stroke={C.grid} vertical={false} />
                    <XAxis dataKey="date" tickLine={false} axisLine={false} minTickGap={40} />
                    <YAxis tickLine={false} axisLine={false} width={52} />
                    <Tooltip contentStyle={{ background: C.ink, border: "none", borderRadius: 6, color: "#fff", fontSize: 12 }} itemStyle={{ color: "#fff" }} />
                    <Line type="monotone" dataKey={k} stroke={C.accent} strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </ChartCard>
            ))}
          </div>
        </>
      )}
      {facts && (
        <Finding label="Suggested next steps">
          <ul className="list-disc space-y-1 pl-5">{facts.split(":").slice(1).join(":").split(";").map((a) => <li key={a}>{a.trim().replace(/\.$/, "")}.</li>)}</ul>
        </Finding>
      )}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <Link to="/assistant" className="inline-flex items-center gap-1.5 text-sm font-medium text-accent">Ask the assistant about this data <ArrowRight size={14} /></Link>
        <details className="text-[0.8rem] text-muted"><summary className="cursor-pointer">Columns detected</summary>
          <div className="mt-2 space-y-0.5">{Object.entries(mapping).map(([k, v]) => <div key={k}><b>{k}</b> ← <code>{v}</code></div>)}</div>
        </details>
      </div>
    </div>
  );
}

function JourneyPanel() {
  const { setDataFact } = useData();
  const [input, setInput] = useState<{ text: string; name: string }>();
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<{ table: ReturnType<typeof attribute>; st: ReturnType<typeof journeyStats> } | { error: string }>();
  useEffect(() => {
    if (!input) return;
    setBusy(true);
    const id = setTimeout(() => {
      try {
        const rows = Papa.parse<Record<string, string>>(input.text, { header: true, skipEmptyLines: true }).data;
        const j = buildJourneys(rows);
        const table = attribute(j), st = journeyStats(j);
        setResult({ table, st });
        setDataFact("journeys", journeyFacts(table, st));
      } catch (e) { setResult({ error: (e as Error).message }); }
      setBusy(false);
    }, 30);
    return () => clearTimeout(id);
  }, [input]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <>
      <Picker samples={JOURNEY_SAMPLES} onText={(text, name) => setInput({ text, name })}
        hint="One row per touchpoint: user_id, timestamp, channel, converted (1 on the touch just before a purchase)." />
      {busy && <p className="mt-6 text-sm text-muted">Rebuilding journeys and running seven attribution models…</p>}
      {result && "error" in result && <div className="card mt-6 border-l-[3px] border-l-bad p-5 text-sm text-bad">Could not read this file. {result.error}</div>}
      {result && "table" in result && !busy && <JourneyDashboard {...result} synthetic={input!.name.toLowerCase().includes("synthetic")} />}
    </>
  );
}

function JourneyDashboard({ table, st, synthetic }: { table: ReturnType<typeof attribute>; st: ReturnType<typeof journeyStats>; synthetic: boolean }) {
  const sh = shares(table);
  const chans = Object.keys(sh).sort((a, b) => sh[b]["Markov chain"] - sh[a]["Markov chain"]);
  const diff = chans.map((c) => ({ label: c, a: sh[c]["Last touch"], b: sh[c]["Markov chain"] })).sort((x, y) => (y.b - y.a) - (x.b - x.a));
  const under = diff[0], over = diff[diff.length - 1];
  const p0 = (x: number) => `${Math.round(x * 100)}%`;
  return (
    <div className="fade-in mt-8">
      {synthetic && <Note>Synthetic sample with known channel roles: Social and Display were built to start journeys; Email and Paid Search to close them.</Note>}
      <div className="mt-3"><Stats items={[
        { label: "Journeys", value: st.journeys.toLocaleString(), note: `${chans.length} channels` },
        { label: "Conversions", value: st.conversions.toLocaleString(), note: `${pct(st.convRate)} of journeys` },
        { label: "Touches before buying", value: st.avgLenConv.toFixed(1), note: `vs ${st.avgLenNon.toFixed(1)} for non-buyers`, accent: true },
        { label: "Single-touch conversions", value: p0(st.singleTouchShare), note: "the rest need an attribution rule" },
      ]} /></div>
      <div className="mt-6"><ChartCard title="Share of conversion credit by channel and model" subtitle="Each column sums to 100%">
        <Heatmap rows={chans} cols={[...MODELS]} value={(r, c) => sh[r][c as (typeof MODELS)[number]]} />
      </ChartCard></div>
      <div className="mt-6 grid gap-5 lg:grid-cols-5">
        <ChartCard className="lg:col-span-3" title="Last-click credit vs data-driven (Markov) credit"><Dumbbell items={diff} aLabel="Last touch" bLabel="Markov chain" /></ChartCard>
        <div className="lg:col-span-2">
          <Finding label="Last-click bias">Last-click gives <b>{under.label}</b> {p0(under.a)} of the credit, but the Markov model gives it {p0(under.b)}: it does more work earlier in journeys. <b>{over.label}</b> is the opposite, {p0(over.a)} under last-click against {p0(over.b)}.</Finding>
          <Table head={["Most common converting paths", "Journeys"]} numeric={[1]} rows={st.topPaths.slice(0, 6).map(([k, v]) => [k, v])} />
        </div>
      </div>
      <details className="card mt-6 p-5 text-sm leading-relaxed">
        <summary className="cursor-pointer font-medium text-ink">How each model assigns credit</summary>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-muted">
          <li><b>First / Last touch:</b> all credit to the first or last interaction.</li>
          <li><b>Linear:</b> split equally across every interaction.</li>
          <li><b>Time decay:</b> more credit closer to the purchase (7-day half-life).</li>
          <li><b>Position based:</b> 40% first, 40% last, 20% shared in the middle.</li>
          <li><b>Markov chain:</b> how far the conversion rate falls if a channel is removed (Anderl et al., 2016).</li>
          <li><b>Shapley value:</b> average marginal contribution across channel combinations (Shao and Li, 2011).</li>
        </ul>
      </details>
      <Link to="/assistant" className="mt-6 inline-flex items-center gap-1.5 text-sm font-medium text-accent">Ask the assistant about these journeys <ArrowRight size={14} /></Link>
    </div>
  );
}
