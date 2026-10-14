import { useState } from "react";
import { Bars, C, PairBars, pctFmt } from "../components/charts";
import { Badge, ChartCard, Container, Finding, Hero, Note, Stats, Table, Tabs } from "../components/ui";
import { Loading, useData } from "../data";

type Tab = "behaviour" | "display" | "validation" | "journeys";
const p = (x: number, d = 1) => `${(x * 100).toFixed(d)}%`;
const n = (x: number) => x.toLocaleString();

export default function Research() {
  const { research: r } = useData();
  const [tab, setTab] = useState<Tab>("behaviour");
  if (!r) return <Loading />;
  return (
    <>
      <Hero eyebrow="Research findings" title="What the data says about journeys, credit and conversion"
        lead="Results from four public datasets and a known-answer simulation. Every number below is computed from the data; all are associations, not proof that a channel caused a sale." />
      <Container className="pt-8">
        <Tabs<Tab> value={tab} onChange={setTab} tabs={[
          { id: "behaviour", label: "Shopper behaviour · RQ2, RQ4" },
          { id: "display", label: "Display ads · last-click gap" },
          { id: "validation", label: "Which model is right? · validation" },
          { id: "journeys", label: "Channel journeys · RQ1" },
        ]} />
        <div className="fade-in" key={tab}>
          {tab === "behaviour" && <Behaviour r={r} />}
          {tab === "display" && <Display r={r} />}
          {tab === "validation" && <Validation r={r} />}
          {tab === "journeys" && <Journeys r={r} />}
        </div>
      </Container>
    </>
  );
}

type R = NonNullable<ReturnType<typeof useData>["research"]>;

function Behaviour({ r }: { r: R }) {
  const u = r.uci;
  const v = Object.fromEntries(u.visitor.map((x) => [x.VisitorType, x]));
  const returningShare = v.Returning_Visitor.sessions / u.sessions;
  const peak = u.month.reduce((a, b) => (b.conversion_rate > a.conversion_rate ? b : a));
  const mo = u.models.without_page_values, mw = u.models.with_page_values;
  const g = Object.fromEntries(u.groups.map((x) => [x.Behaviour as string, x]));
  const show = ["Product pages viewed", "Time on product pages (s)", "Account/admin pages viewed", "Bounce rate", "Exit rate", "Page value"];
  const fmt = (b: string, x: number) => (b.includes("(s)") ? `${(x / 60).toFixed(1)} min` : b.includes("rate") ? x.toFixed(3) : x.toFixed(1));
  return (
    <>
      <p className="mb-4 text-sm text-muted">UCI Online Shoppers Purchasing Intention (Sakar et al., 2019) · {n(u.sessions)} sessions after removing duplicates</p>
      <Stats items={[
        { label: "Overall conversion", value: p(u.conversion_rate), note: `${n(u.purchases)} purchasing sessions` },
        { label: "New visitors convert at", value: p(v.New_Visitor.conversion_rate), note: `vs ${p(v.Returning_Visitor.conversion_rate)} for returning`, accent: true },
        { label: "Peak month", value: peak.Month, note: `${p(peak.conversion_rate)} conversion` },
        { label: "Prediction (ROC-AUC)", value: mo.rf_auc.toFixed(2), note: "early-session signals only" },
      ]} />
      <div className="mt-6 grid gap-5 lg:grid-cols-2">
        <ChartCard title="Conversion rate by visitor type">
          <Bars data={u.visitor.map((x) => ({ k: x.VisitorType.replace("_Visitor", "").replace("Returning", "Returning"), v: x.conversion_rate }))} x="k" y="v"
            highlight={(x) => x.k === "New"} />
        </ChartCard>
        <ChartCard title="Conversion rate by traffic source" subtitle="Anonymised source codes with 100+ sessions">
          <Bars horizontal height={320} data={u.traffic.map((x) => ({ k: `Source ${x.TrafficType}`, v: x.conversion_rate }))} x="k" y="v" highlight={(_, i) => i < 3} />
        </ChartCard>
      </div>
      <Finding>Returning visitors are {p(returningShare, 0)} of traffic but convert at only {p(v.Returning_Visitor.conversion_rate)}, against {p(v.New_Visitor.conversion_rate)} for new visitors (χ² p &lt; 0.001). They are the largest re-engagement opportunity.</Finding>
      <ChartCard title="Conversion rate by month" subtitle="January and April are not in the dataset">
        <Bars data={u.month.map((x) => ({ k: x.Month, v: x.conversion_rate }))} x="k" y="v" highlight={(x) => x.k === peak.Month} />
      </ChartCard>
      <div className="mt-6 grid gap-5 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <Table head={["Behaviour (mean per session)", "Buyers", "Non-buyers", "p-value"]} numeric={[1, 2, 3]}
            rows={show.map((b) => [b.replace(" (s)", ""), fmt(b, Number(g[b]["Mean (converted)"])), fmt(b, Number(g[b]["Mean (not converted)"])),
              Number(g[b]["p-value"]) === 0 ? "< 1e-300" : Number(g[b]["p-value"]).toExponential(1)])} />
          <Note>Two-sided Mann-Whitney U. All ten behaviours measured differ at p &lt; 0.05.</Note>
        </div>
        <ChartCard className="lg:col-span-2" title="Strongest purchase signals" subtitle="Random forest permutation importance, without PageValues">
          <Bars horizontal height={300} format={(x) => x.toFixed(3)} data={mo.importance.slice(0, 6).map((x) => ({ k: x.feature.replace(" (s)", ""), v: x.importance }))} x="k" y="v" highlight={(_, i) => i < 3} />
        </ChartCard>
      </div>
      <div className="mt-6">
        <Table head={["Model", "With PageValues", "Without PageValues"]} numeric={[1, 2]} rows={[
          ["Logistic regression", mw.logit_auc.toFixed(3), mo.logit_auc.toFixed(3)],
          ["Random forest", mw.rf_auc.toFixed(3), mo.rf_auc.toFixed(3)],
          ["Gradient boosting", mw.hgb_auc.toFixed(3), mo.hgb_auc.toFixed(3)],
        ]} />
        <Note>ROC-AUC on a stratified 25% hold-out. PageValues is computed from pages seen before a purchase, so it partly contains the outcome; the right-hand column is the honest estimate.</Note>
      </div>
    </>
  );
}

function Display({ r }: { r: R }) {
  const c = r.criteo;
  const hours = Object.entries(c.attributed_by_hours_since_last_click).map(([k, x]) => ({ k, v: x.share, n: x.n }));
  const touches = Object.entries(c.attributed_by_touches).map(([k, x]) => ({ k: k === "6" ? "6+" : k, v: x.share }));
  return (
    <>
      <p className="mb-4 text-sm text-muted">Criteo Attribution Modeling for Bidding (Diemert et al., 2017) · 30 days of live display-advertising traffic</p>
      <Stats items={[
        { label: "Impressions", value: `${(c.impressions / 1e6).toFixed(1)}M`, note: `${(c.users / 1e6).toFixed(1)}M users, ${c.campaigns} campaigns` },
        { label: "Conversions", value: n(c.conversions), note: `${c.touches_mean.toFixed(2)} clicks per converting journey` },
        { label: "Credited to Criteo", value: p(c.attributed_share), note: "under the advertiser's last-click rule", accent: true },
        { label: "Single-campaign journeys", value: p(c.single_campaign_share), note: "cross-campaign attribution not possible" },
      ]} />
      <div className="mt-6 grid gap-5 lg:grid-cols-5">
        <ChartCard className="lg:col-span-3" title="Share of conversions credited to Criteo, by time since its last click">
          <Bars height={300} data={hours} x="k" y="v" format={pctFmt(0)} colors={(_, i) => (i === 0 ? C.accent : i === hours.length - 1 ? C.bad : C.quiet)} />
        </ChartCard>
        <ChartCard className="lg:col-span-2" title="…and by number of Criteo clicks" subtitle="Barely changes">
          <Bars height={300} data={touches} x="k" y="v" format={pctFmt(0)} />
        </ChartCard>
      </div>
      <Finding label="Finding · last-click rewards recency">
        Every one of these {n(c.conversions)} conversions followed a Criteo click, yet only {p(c.attributed_share, 0)} were credited to Criteo. Credit falls from {p(hours[0].v, 0)} when the purchase came within an hour of the click to {p(hours[hours.length - 1].v, 0)} after 7–31 days, while extra clicks move it by only a few points. Under last-click, timing rather than contribution decides which platform gets the sale.
      </Finding>
      <Note>Validity notes: {p(c.single_campaign_share)} of conversions involve one campaign and the public sample keeps only clicked impressions for converting users, so this dataset is used for the last-click gap and recency effect, not for comparing channels.</Note>
    </>
  );
}

function Validation({ r }: { r: R }) {
  const s = r.simulation;
  const rows = s.immediate.summary.map((x, i) => ({ model: x.model, imm: x.mae_pp, car: s.carryover.summary[i].mae_pp, ri: x.spearman, rc: s.carryover.summary[i].spearman }));
  const bestI = rows.reduce((a, b) => (b.imm < a.imm ? b : a)), bestC = rows.reduce((a, b) => (b.car < a.car ? b : a));
  const tiedC = rows.filter((x) => x.car - bestC.car < 0.1);
  return (
    <>
      <p className="mb-4 max-w-3xl text-sm leading-relaxed text-muted">Real data has no ground truth for attribution. We simulated customer journeys in six random "worlds" per scenario where we set each channel's effect, measured each channel's true contribution by switching it off, and scored every model by how far its credit shares fall from the truth.</p>
      <div className="grid gap-5 lg:grid-cols-2">
        <ChartCard title="Error when ads act immediately" subtitle="Mean absolute error in credit share, percentage points (lower is better)">
          <Bars horizontal height={300} format={(x) => `${x.toFixed(1)} pp`} data={rows.map((x) => ({ k: x.model, v: x.imm }))} x="k" y="v" highlight={(x) => x.k === bestI.model} />
        </ChartCard>
        <ChartCard title="Error when ads act with carry-over" subtitle="Awareness now, purchase on a later visit">
          <Bars horizontal height={300} format={(x) => `${x.toFixed(1)} pp`} data={rows.map((x) => ({ k: x.model, v: x.car }))} x="k" y="v" highlight={(x) => x.k === bestC.model} />
        </ChartCard>
      </div>
      <Finding label="Finding · no universally best model">
        When ads act immediately, <b>{bestI.model}</b> is closest to the truth ({bestI.imm.toFixed(1)} pp). With carry-over effects, last-touch error rises to {rows[1].car.toFixed(1)} pp and its rank agreement drops from {rows[1].ri.toFixed(2)} to {rows[1].rc.toFixed(2)}, while {tiedC.map((m, i) => <span key={m.model}>{i ? " and " : ""}<b>{m.model}</b></span>)} {tiedC.length > 1 ? "become the most accurate" : "becomes best"} ({bestC.car.toFixed(1)} pp). First touch is worst in both. The right model depends on how a business's advertising actually works, which is why ChannelTrace shows all seven side by side.
      </Finding>
      <Table head={["Model", "Error · immediate", "Rank corr.", "Error · carry-over", "Rank corr."]} numeric={[1, 2, 3, 4]}
        rows={rows.map((x) => [x.model, `${x.imm.toFixed(1)} pp`, x.ri.toFixed(2), `${x.car.toFixed(1)} pp`, x.rc.toFixed(2)])} />
      <Note>3,000 simulated users per world; true contribution = conversions lost when the channel's effect is removed, using common random numbers. Spearman rank correlation between model and true shares.</Note>
    </>
  );
}

function Journeys({ r }: { r: R }) {
  if (!r.ga360)
    return (
      <div className="card p-8">
        <Badge kind="pending">Data access pending</Badge>
        <h3 className="mt-3 font-sans text-lg font-semibold">Google Analytics 360 multi-session journeys</h3>
        <p className="mt-2 max-w-2xl text-sm leading-relaxed text-muted">The Google Merchandise Store sample holds 12 months of sessions with a persistent visitor ID and named channels (Organic Search, Paid Search, Social, Referral, Display, Affiliates, Direct). It is the only public dataset with several named channels per customer, and it is queried through Google BigQuery's free sandbox. Results will appear here once the extraction runs.</p>
        <p className="mt-4 text-sm text-muted">Meanwhile, try the attribution engine on journey data in <a className="font-medium text-accent underline" href="/analyse">Analyse your data</a>.</p>
      </div>
    );
  return <GA360 data={r.ga360} />;
}

type GA = {
  visitors: number; sessions: number; conversions: number; conv_rate: number; period: string;
  multi_session_share: number; multi_channel_share: number; sessions_mean: number; nonconv_sessions_mean: number;
  shares: Record<string, Record<string, number>>; top_paths: [string, number][];
  multi_channel: { journeys: number; shares: Record<string, Record<string, number>>; top_paths: [string, number][] };
  referral_no_source: { converting_share: number; true_direct_sessions: number; sessions: number };
};

function GA360({ data }: { data: Record<string, unknown> }) {
  const d = data as unknown as GA;
  const models = ["First touch", "Last touch", "Linear", "Time decay", "Position based", "Markov chain", "Shapley value"];
  const chans = Object.keys(d.shares).filter((c) => d.shares[c]["Linear"] > 0.0005).sort((a, b) => d.shares[b]["Linear"] - d.shares[a]["Linear"]);
  const mc = d.multi_channel.shares;
  const mchans = Object.keys(mc).filter((c) => mc[c]["Linear"] > 0.005).sort((a, b) => mc[b]["Linear"] - mc[a]["Linear"]);
  return (
    <>
      <Stats items={[
        { label: "Visitors", value: n(d.visitors), note: "Google Merchandise Store, 12 months" },
        { label: "Converting journeys", value: n(d.conversions), note: `${p(d.conv_rate)} of journeys` },
        { label: "Took several sessions", value: p(d.multi_session_share, 0), note: `${d.sessions_mean.toFixed(2)} sessions on average` },
        { label: "Used several channels", value: p(d.multi_channel_share, 0), accent: true, note: `${n(d.multi_channel.journeys)} journeys` },
      ]} />
      <Finding label="Finding · models disagree where channels mix">
        Most buyers came back through the channel that first brought them, so on the whole sample the seven models broadly agree. In the {n(d.multi_channel.journeys)} journeys that mixed channels they do not: first touch gives Direct {p(mc.Direct["First touch"], 0)} of the credit and last touch {p(mc.Direct["Last touch"], 0)}, while Referral goes from {p(mc.Referral["First touch"], 0)} to {p(mc.Referral["Last touch"], 0)}.
      </Finding>
      <div className="grid gap-5 lg:grid-cols-2">
        <ChartCard title="Multi-channel journeys: first touch vs last touch" subtitle={`Credit share by channel, ${n(d.multi_channel.journeys)} converting journeys with more than one channel`}>
          <PairBars data={mchans.map((c) => ({ channel: c, first: mc[c]["First touch"], last: mc[c]["Last touch"] }))} x="channel" a="first" b="last" aLabel="First touch" bLabel="Last touch" height={300} />
        </ChartCard>
        <ChartCard title="Most common multi-channel paths" subtitle="Sessions in order, up to the first purchase">
          <div className="space-y-2.5">
            {d.multi_channel.top_paths.slice(0, 7).map(([path, k]) => (
              <div key={path} className="flex items-baseline justify-between gap-4 border-b border-rule pb-2 text-sm last:border-0">
                <span className="text-ink">{path.split(" > ").join(" → ")}</span>
                <span className="whitespace-nowrap tabular-nums text-muted">{n(k)}</span>
              </div>
            ))}
          </div>
        </ChartCard>
      </div>
      <h3 className="mb-3 mt-8 font-sans text-[0.95rem] font-semibold text-ink">Credit share by channel, all {n(d.conversions)} converting journeys</h3>
      <Table head={["Channel", ...models]} numeric={models.map((_, i) => i + 1)} rows={chans.map((c) => [c, ...models.map((m) => p(d.shares[c][m]))])} />
      <Note>
        Journeys follow a visitor across sessions (cookie-based ID) up to the first purchase. Caveats: Google Analytics labels a returning direct visit with the visitor's previous campaign ({n(d.referral_no_source.true_direct_sessions)} of {n(d.referral_no_source.sessions)} Referral sessions are flagged as direct visits), so Direct rarely appears late in a journey; and {p(d.referral_no_source.converting_share, 0)} of converting Referral sessions record no referring site.
      </Note>
    </>
  );
}
