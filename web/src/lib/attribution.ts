// Multi-touch attribution on customer-journey data, run in the browser.
// Input rows: user_id, timestamp, channel, converted (1 on the touch just before a purchase).
// Models: first, last, linear, time decay, position based, Markov removal effect (Anderl et al., 2016)
// and Shapley value (Shao & Li, 2011). Every model distributes exactly the total number of conversions.

export const MODELS = [
  "First touch", "Last touch", "Linear", "Time decay", "Position based", "Markov chain", "Shapley value",
] as const;
export type Model = (typeof MODELS)[number];

export interface Journey { user: string; path: string[]; times: number[]; converted: boolean }
export type CreditTable = Record<string, Record<Model, number>>; // channel -> model -> conversions

export function buildJourneys(rows: Record<string, string>[]): Journey[] {
  const norm = (r: Record<string, string>) => {
    const o: Record<string, string> = {};
    for (const [k, v] of Object.entries(r)) o[k.trim().toLowerCase().replace(/\s+/g, "_")] = String(v ?? "").trim();
    return o;
  };
  const clean = rows.map(norm);
  const need = ["user_id", "timestamp", "channel", "converted"];
  const missing = need.filter((c) => !(c in (clean[0] ?? {})));
  if (missing.length) throw new Error(`Journey file needs columns ${need.join(", ")}; missing ${missing.join(", ")}`);
  const byUser = new Map<string, { t: number; ch: string; conv: boolean }[]>();
  for (const r of clean) {
    const t = Date.parse(r.timestamp.replace(" ", "T"));
    if (!r.user_id || Number.isNaN(t) || !r.channel) continue;
    const conv = ["1", "true", "yes"].includes(r.converted.toLowerCase());
    if (!byUser.has(r.user_id)) byUser.set(r.user_id, []);
    byUser.get(r.user_id)!.push({ t, ch: r.channel, conv });
  }
  const out: Journey[] = [];
  for (const [user, touches] of byUser) {
    touches.sort((a, b) => a.t - b.t);
    const hit = touches.findIndex((x) => x.conv);
    const kept = hit >= 0 ? touches.slice(0, hit + 1) : touches;
    out.push({ user, path: kept.map((x) => x.ch), times: kept.map((x) => x.t), converted: hit >= 0 });
  }
  return out;
}

function ruleBased(conv: Journey[], halfLifeDays: number) {
  const credit: Record<string, Record<string, number>> = {};
  const add = (m: string, ch: string, v: number) => {
    credit[m] ??= {};
    credit[m][ch] = (credit[m][ch] ?? 0) + v;
  };
  for (const { path: p, times: t } of conv) {
    const n = p.length;
    add("First touch", p[0], 1);
    add("Last touch", p[n - 1], 1);
    p.forEach((ch) => add("Linear", ch, 1 / n));
    const w = t.map((x) => 0.5 ** ((t[n - 1] - x) / 86400000 / halfLifeDays));
    const ws = w.reduce((a, b) => a + b, 0);
    p.forEach((ch, i) => add("Time decay", ch, w[i] / ws));
    const pos = n === 1 ? [1] : n === 2 ? [0.5, 0.5] : [0.4, ...Array(n - 2).fill(0.2 / (n - 2)), 0.4];
    p.forEach((ch, i) => add("Position based", ch, pos[i]));
  }
  return credit;
}

// Solve A x = b by Gaussian elimination with partial pivoting.
function solve(A: number[][], b: number[]): number[] {
  const n = b.length;
  const M = A.map((row, i) => [...row, b[i]]);
  for (let c = 0; c < n; c++) {
    let piv = c;
    for (let r = c + 1; r < n; r++) if (Math.abs(M[r][c]) > Math.abs(M[piv][c])) piv = r;
    [M[c], M[piv]] = [M[piv], M[c]];
    if (Math.abs(M[c][c]) < 1e-12) continue;
    for (let r = 0; r < n; r++) {
      if (r === c) continue;
      const f = M[r][c] / M[c][c];
      for (let k = c; k <= n; k++) M[r][k] -= f * M[c][k];
    }
  }
  return M.map((row, i) => (Math.abs(row[i]) < 1e-12 ? 0 : row[n] / row[i]));
}

function markovConvProb(journeys: Journey[], channels: string[], removed?: string): number {
  const states = ["start", ...channels];
  const idx = new Map(states.map((s, i) => [s, i]));
  const n = states.length;
  const trans = Array.from({ length: n }, () => Array(n + 2).fill(0)); // last two: conversion, null
  for (const j of journeys) {
    const seq = ["start", ...j.path];
    for (let i = 0; i < seq.length - 1; i++) trans[idx.get(seq[i])!][idx.get(seq[i + 1])!] += 1;
    trans[idx.get(seq[seq.length - 1])!][j.converted ? n : n + 1] += 1;
  }
  if (removed) {
    const r = idx.get(removed)!;
    trans[r] = Array(n + 2).fill(0);
    trans[r][n + 1] = 1;
  }
  const P = trans.map((row) => {
    const s = row.reduce((a, b) => a + b, 0);
    return row.map((v) => (s > 0 ? v / s : 0));
  });
  const A = P.map((row, i) => row.slice(0, n).map((q, k) => (i === k ? 1 : 0) - q));
  const x = solve(A, P.map((row) => row[n]));
  return x[0];
}

function markov(journeys: Journey[], channels: string[], total: number) {
  const base = markovConvProb(journeys, channels);
  const effect: Record<string, number> = {};
  for (const c of channels) effect[c] = base > 0 ? Math.max(0, 1 - markovConvProb(journeys, channels, c) / base) : 0;
  const s = Object.values(effect).reduce((a, b) => a + b, 0);
  return Object.fromEntries(channels.map((c) => [c, s ? (total * effect[c]) / s : 0]));
}

function shapley(conv: Journey[], channels: string[]) {
  const n = channels.length;
  if (n > 12) throw new Error("Shapley value is limited to 12 channels");
  const bit = new Map(channels.map((c, i) => [c, 1 << i]));
  const counts = new Map<number, number>();
  for (const j of conv) {
    const m = j.path.reduce((acc, c) => acc | bit.get(c)!, 0);
    counts.set(m, (counts.get(m) ?? 0) + 1);
  }
  const v = new Float64Array(1 << n);
  for (let S = 0; S < 1 << n; S++) {
    let tot = 0;
    for (const [m, cnt] of counts) if ((m & S) === m) tot += cnt;
    v[S] = tot;
  }
  const fact = [1];
  for (let i = 1; i <= n; i++) fact[i] = fact[i - 1] * i;
  const phi: Record<string, number> = {};
  channels.forEach((c, i) => {
    let total = 0;
    for (let S = 0; S < 1 << n; S++) {
      if (S & (1 << i)) continue;
      let k = 0;
      for (let x = S; x; x &= x - 1) k++;
      total += ((fact[k] * fact[n - k - 1]) / fact[n]) * (v[S | (1 << i)] - v[S]);
    }
    phi[c] = total;
  });
  return phi;
}

export function attribute(journeys: Journey[], halfLifeDays = 7): CreditTable {
  const conv = journeys.filter((j) => j.converted);
  const channels = [...new Set(journeys.flatMap((j) => j.path))].sort();
  const credit: Record<string, Record<string, number>> = ruleBased(conv, halfLifeDays);
  credit["Markov chain"] = markov(journeys, channels, conv.length);
  credit["Shapley value"] = shapley(conv, channels);
  const table: CreditTable = {};
  for (const ch of channels) {
    table[ch] = {} as Record<Model, number>;
    for (const m of MODELS) table[ch][m] = credit[m]?.[ch] ?? 0;
  }
  return table;
}

export function shares(table: CreditTable): CreditTable {
  const out: CreditTable = {};
  const sums = Object.fromEntries(MODELS.map((m) => [m, Object.values(table).reduce((a, r) => a + r[m], 0)]));
  for (const [ch, row] of Object.entries(table)) {
    out[ch] = {} as Record<Model, number>;
    for (const m of MODELS) out[ch][m] = sums[m] ? row[m] / sums[m] : 0;
  }
  return out;
}

export function journeyStats(journeys: Journey[]) {
  const conv = journeys.filter((j) => j.converted);
  const non = journeys.filter((j) => !j.converted);
  const mean = (a: number[]) => (a.length ? a.reduce((x, y) => x + y, 0) / a.length : 0);
  const pathCounts = new Map<string, number>();
  for (const j of conv) {
    const k = j.path.join(" → ");
    pathCounts.set(k, (pathCounts.get(k) ?? 0) + 1);
  }
  return {
    journeys: journeys.length,
    conversions: conv.length,
    convRate: journeys.length ? conv.length / journeys.length : 0,
    avgLenConv: mean(conv.map((j) => j.path.length)),
    avgLenNon: mean(non.map((j) => j.path.length)),
    singleTouchShare: conv.length ? conv.filter((j) => j.path.length === 1).length / conv.length : 0,
    topPaths: [...pathCounts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8),
  };
}

export function journeyFacts(table: CreditTable, st: ReturnType<typeof journeyStats>): string {
  const sh = shares(table);
  const chans = Object.keys(sh).sort((a, b) => sh[b]["Markov chain"] - sh[a]["Markov chain"]);
  const diff = chans.map((c) => [c, sh[c]["Markov chain"] - sh[c]["Last touch"]] as const).sort((a, b) => a[1] - b[1]);
  const under = diff[diff.length - 1][0], over = diff[0][0];
  const p = (x: number) => `${Math.round(x * 100)}%`;
  return [
    `UPLOADED JOURNEYS: ${st.journeys.toLocaleString()} customer journeys, ${st.conversions.toLocaleString()} conversions ` +
      `(${(st.convRate * 100).toFixed(1)}%). Converting journeys average ${st.avgLenConv.toFixed(1)} touchpoints vs ` +
      `${st.avgLenNon.toFixed(1)} for non-converting; ${p(st.singleTouchShare)} of conversions had a single touch.`,
    `UPLOADED TOP PATHS: ${st.topPaths.slice(0, 5).map(([k, n]) => `${k} (${n})`).join("; ")}.`,
    `UPLOADED ATTRIBUTION SHARES (last touch / linear / Markov / Shapley): ` +
      chans.map((c) => `${c}: ${p(sh[c]["Last touch"])} / ${p(sh[c]["Linear"])} / ${p(sh[c]["Markov chain"])} / ${p(sh[c]["Shapley value"])}`).join("; ") + ".",
    `UPLOADED LAST-CLICK BIAS: last-click most under-credits ${under} (Markov ${p(sh[under]["Markov chain"])} vs last touch ` +
      `${p(sh[under]["Last touch"])}) and most over-credits ${over} (Markov ${p(sh[over]["Markov chain"])} vs last touch ${p(sh[over]["Last touch"])}).`,
    `ACTION (suggestions for your channels): do not cut ${under} based on last-click reports alone, because it contributes ` +
      `more to journeys than last-click shows; treat ${over}'s last-click numbers with caution, as it often closes journeys ` +
      `that other channels started. Compare models before moving budget.`,
  ].join("\n");
}
