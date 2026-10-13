// Plug-and-play ad performance analysis for Google Ads, Meta Ads and similar CSV exports.
import Papa from "papaparse";

const ALIASES: Record<string, string[]> = {
  campaign: ["campaign", "campaign name", "xyz_campaign_id"],
  group: ["ad group", "ad group name", "ad set name", "ad set", "fb_campaign_id"],
  spend: ["cost", "spend", "spent", "amount spent", "amount spent (usd)", "amount spent (inr)", "amount spent (eur)", "amount spent (gbp)"],
  impressions: ["impressions", "impr.", "impr"],
  clicks: ["clicks", "link clicks", "clicks (all)"],
  conversions: ["conversions", "approved_conversion", "results", "purchases", "website purchases", "conv."],
  revenue: ["conv. value", "conversion value", "all conv. value", "purchases conversion value", "website purchases conversion value", "revenue", "purchase conversion value"],
  date: ["day", "date", "reporting starts"],
  age: ["age"],
  gender: ["gender"],
};
const REQUIRED = ["campaign", "spend", "clicks", "conversions"];
const norm = (c: string) => c.trim().toLowerCase().replace(/\s+/g, " ");

function match(columns: string[]): Record<string, string> {
  const normed = new Map(columns.map((c) => [norm(c), c]));
  const found: Record<string, string> = {};
  for (const [key, names] of Object.entries(ALIASES)) {
    const hit = names.find((n) => normed.has(n));
    if (hit) found[key] = normed.get(hit)!;
    else if (key === "spend") {
      const any = [...normed.entries()].find(([n]) => n.startsWith("amount spent"));
      if (any) found[key] = any[1];
    }
  }
  return found;
}

export function detectPlatform(columns: string[]): string {
  const n = new Set(columns.map(norm));
  if (n.has("xyz_campaign_id")) return "Facebook Ads (Kaggle export format)";
  if ([...n].some((c) => c.startsWith("amount spent")) || n.has("ad set name") || n.has("reporting starts")) return "Meta Ads Manager";
  if (n.has("impr.") || n.has("conv.") || n.has("ad group") || (n.has("cost") && n.has("conversions"))) return "Google Ads";
  return "Generic ad report";
}

const num = (v: unknown) => {
  if (typeof v === "number") return v;
  const s = String(v ?? "").replace(/[^\d.-]/g, "");
  const x = parseFloat(s);
  return Number.isFinite(x) ? x : 0;
};

export interface AdRow { campaign: string; group?: string; spend: number; impressions: number; clicks: number; conversions: number; revenue?: number; date?: string; age?: string; gender?: string }

export function parseAds(text: string): { rows: AdRow[]; platform: string; mapping: Record<string, string> } {
  const lines = text.replace(/\r\n?/g, "\n").split("\n");
  let header = 0;
  for (let i = 0; i < Math.min(15, lines.length); i++) {
    const cells = lines[i].split(/[,\t]/).map((c) => c.trim().replace(/^"|"$/g, ""));
    if (Object.keys(match(cells)).length >= 3) { header = i; break; }
  }
  const body = lines.slice(header).join("\n");
  const parsed = Papa.parse<Record<string, string>>(body, { header: true, skipEmptyLines: true });
  const columns = parsed.meta.fields ?? [];
  const mapping = match(columns);
  const missing = REQUIRED.filter((k) => !(k in mapping));
  if (missing.length) throw new Error(`Could not find column(s) for ${missing.join(", ")}. Found: ${columns.join(", ")}`);
  const rows: AdRow[] = parsed.data
    .filter((r) => !String(r[columns[0]] ?? "").toLowerCase().startsWith("total"))
    .map((r) => ({
      campaign: String(r[mapping.campaign] ?? ""),
      group: mapping.group ? String(r[mapping.group]) : undefined,
      spend: num(r[mapping.spend]),
      impressions: mapping.impressions ? num(r[mapping.impressions]) : NaN,
      clicks: num(r[mapping.clicks]),
      conversions: num(r[mapping.conversions]),
      revenue: mapping.revenue ? num(r[mapping.revenue]) : undefined,
      date: mapping.date ? String(r[mapping.date]) : undefined,
      age: mapping.age ? String(r[mapping.age]) : undefined,
      gender: mapping.gender ? String(r[mapping.gender]) : undefined,
    }))
    .filter((r) => r.campaign);
  return { rows, platform: detectPlatform(columns), mapping };
}

export interface Metrics { spend: number; impressions: number; clicks: number; conversions: number; revenue: number; ctr: number; cpc: number; cvr: number; cpa: number; roas: number }
export interface CampaignRow extends Metrics { campaign: string; spendShare: number; convShare: number; verdict: Verdict }
export type Verdict = "Scale candidate" | "On track" | "Expensive" | "No conversions";

const div = (a: number, b: number) => (b > 0 ? a / b : NaN);
function metrics(rows: AdRow[]): Metrics {
  const s = rows.reduce((acc, r) => ({
    spend: acc.spend + r.spend, impressions: acc.impressions + (Number.isNaN(r.impressions) ? 0 : r.impressions),
    clicks: acc.clicks + r.clicks, conversions: acc.conversions + r.conversions, revenue: acc.revenue + (r.revenue ?? 0),
  }), { spend: 0, impressions: 0, clicks: 0, conversions: 0, revenue: 0 });
  return { ...s, ctr: div(s.clicks, s.impressions), cpc: div(s.spend, s.clicks), cvr: div(s.conversions, s.clicks), cpa: div(s.spend, s.conversions), roas: div(s.revenue, s.spend) };
}
const groupBy = <K extends string>(rows: AdRow[], key: (r: AdRow) => K) => {
  const m = new Map<K, AdRow[]>();
  for (const r of rows) { const k = key(r); if (!m.has(k)) m.set(k, []); m.get(k)!.push(r); }
  return m;
};

export interface AdSummary {
  totals: Metrics; campaigns: CampaignRow[]; hasRevenue: boolean; rows: number;
  zeroCount: number; zeroSpend: number; zeroShare: number; wasteUnit: string;
  age?: (Metrics & { key: string })[]; gender?: (Metrics & { key: string })[]; daily?: (Metrics & { date: string })[];
}

export function summarise(rows: AdRow[]): AdSummary {
  const totals = metrics(rows);
  const hasRevenue = rows.some((r) => r.revenue !== undefined);
  const acct = totals.cpa;
  const verdict = (m: Metrics): Verdict =>
    m.spend > 0 && m.conversions === 0 ? "No conversions" : m.cpa > 1.5 * acct ? "Expensive" : m.cpa < 0.75 * acct ? "Scale candidate" : "On track";
  const campaigns = [...groupBy(rows, (r) => r.campaign)].map(([campaign, rs]) => {
    const m = metrics(rs);
    return { campaign, ...m, spendShare: div(m.spend, totals.spend), convShare: div(m.conversions, totals.conversions), verdict: verdict(m) };
  }).sort((a, b) => b.spend - a.spend);
  const hasGroup = rows.some((r) => r.group);
  const units = hasGroup ? [...groupBy(rows, (r) => `${r.campaign}||${r.group}`).values()].map(metrics) : rows.map((r) => metrics([r]));
  const zero = units.filter((m) => m.spend > 0 && m.conversions === 0);
  const zeroSpend = zero.reduce((a, m) => a + m.spend, 0);
  const seg = (k: "age" | "gender") => rows.some((r) => r[k]) ? [...groupBy(rows, (r) => r[k] ?? "")].map(([key, rs]) => ({ key, ...metrics(rs) })).sort((a, b) => a.key.localeCompare(b.key)) : undefined;
  const hasDate = rows.some((r) => r.date && !Number.isNaN(Date.parse(r.date)));
  return {
    totals, campaigns, hasRevenue, rows: rows.length,
    zeroCount: zero.length, zeroSpend, zeroShare: div(zeroSpend, totals.spend),
    wasteUnit: hasGroup ? "ad sets or ad groups" : hasDate ? "campaign-days" : "report rows",
    age: seg("age"), gender: seg("gender"),
    daily: hasDate ? [...groupBy(rows, (r) => r.date ?? "")].map(([date, rs]) => ({ date, ...metrics(rs) })).sort((a, b) => a.date.localeCompare(b.date)) : undefined,
  };
}

export const money = (x: number) => (Number.isFinite(x) ? x.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "–");
export const pct = (x: number, d = 1) => (Number.isFinite(x) ? `${(x * 100).toFixed(d)}%` : "–");

export function adFacts(s: AdSummary, platform: string): string {
  const t = s.totals, c = s.campaigns;
  const lines = [
    `UPLOADED AD DATA: ${platform}, ${s.rows.toLocaleString()} rows, ${c.length} campaigns. Total spend ${money(t.spend)}, ` +
      `${t.impressions.toLocaleString()} impressions, ${t.clicks.toLocaleString()} clicks, ${t.conversions.toLocaleString()} conversions. ` +
      `CTR ${pct(t.ctr, 2)}, CPC ${money(t.cpc)}, conversion rate ${pct(t.cvr, 2)}, CPA ${money(t.cpa)}` + (s.hasRevenue ? `, ROAS ${t.roas.toFixed(2)}x.` : "."),
    `UPLOADED CAMPAIGNS (by spend): ` + c.map((r) => `${r.campaign}: spend ${money(r.spend)} (${pct(r.spendShare, 0)}), ${r.conversions} conversions, CPA ${money(r.cpa)}` +
      (s.hasRevenue && Number.isFinite(r.roas) ? `, ROAS ${r.roas.toFixed(2)}x` : "") + `, verdict ${r.verdict}`).join("; ") + ".",
    `UPLOADED WASTE: ${s.zeroCount} ${s.wasteUnit} spent money with zero conversions, totalling ${money(s.zeroSpend)} (${pct(s.zeroShare)} of spend).`,
  ];
  const acts: string[] = [];
  const scale = c.filter((r) => r.verdict === "Scale candidate"), costly = c.filter((r) => r.verdict === "Expensive" || r.verdict === "No conversions");
  if (costly.length && scale.length) acts.push(`test moving part of the budget from ${costly.slice(0, 2).map((r) => `${r.campaign} (CPA ${money(r.cpa)})`).join(", ")} to ${scale.slice(0, 2).map((r) => `${r.campaign} (CPA ${money(r.cpa)})`).join(", ")}`);
  else if (scale.length) acts.push(`test raising budget on ${scale.slice(0, 2).map((r) => r.campaign).join(", ")}, which convert well below the account CPA`);
  if (s.zeroCount) acts.push(`review the ${s.zeroCount} ${s.wasteUnit} with spend but no conversions (${money(s.zeroSpend)} of spend)`);
  for (const [k, seg] of [["age", s.age], ["gender", s.gender]] as const) {
    if (!seg) continue;
    const valid = seg.filter((x) => Number.isFinite(x.cpa));
    const best = valid.reduce((a, b) => (b.cpa < a.cpa ? b : a));
    const worst = valid.reduce((a, b) => (b.cpa > a.cpa ? b : a));
    acts.push(`weight targeting toward ${k} ${best.key}, the lowest CPA segment`);
    lines.push(`UPLOADED BY ${k.toUpperCase()}: lowest CPA ${best.key} (${money(best.cpa)}), highest CPA ${worst.key} (${money(worst.cpa)}). ` +
      seg.map((x) => `${x.key}: CPA ${money(x.cpa)}, CVR ${pct(x.cvr)}`).join("; ") + ".");
  }
  if (acts.length) lines.push(`ACTION (suggestions for your campaigns): ${acts.join("; ")}. Test changes gradually and re-check results, since past CPA does not guarantee future performance.`);
  return lines.join("\n");
}
