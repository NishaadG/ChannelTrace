// ChannelTrace assistant. Uses a free generative model through /api/chat when the site has a key configured;
// otherwise a built-in TF-IDF retrieval model that quotes the most relevant computed facts. Only the fact
// sheet (aggregated results) is ever used; raw uploaded rows are never sent anywhere.

const STOP = new Set("a an and are as at be by can do does for from has have how i in is it its me my of on or our should so that the their them then there these this to us was we what when where which who why will with you your".split(" "));
const SYNONYMS: Record<string, string> = {
  waste: "zero conversions spent", wasted: "zero conversions spent", budget: "spend shift budget",
  best: "lowest cpa scale candidate best", worst: "highest cpa expensive worst", cut: "expensive zero conversions pause",
  improve: "action suggestion", should: "action suggestion", recommend: "action suggestion", suggest: "action suggestion",
  channel: "channel attribution", credit: "attribution credited", undervalued: "under-credits", overvalued: "over-credits",
  undervalue: "under-credits", roi: "roas", audience: "age gender segment targeting", target: "age gender segment targeting",
  segment: "age gender", when: "month season", summary: "dataset overall total", summarise: "dataset overall total",
  summarize: "dataset overall total", limitation: "caveats", display: "criteo display", recency: "hours recency last-click",
  model: "model validation simulation error", accurate: "validation simulation error", validation: "simulation error",
};

const tokens = (s: string) => s.toLowerCase().replace(/[^a-z0-9%.\- ]/g, " ").split(/\s+/).filter((w) => w && !STOP.has(w));
const grams = (s: string) => { const t = tokens(s); return [...t, ...t.slice(1).map((w, i) => `${t[i]} ${w}`)]; };

function chunks(facts: string): [number, string][] {
  const out: [number, string][] = [];
  facts.split("\n").filter((l) => l.trim()).forEach((line, n) => {
    out.push([n, line]);
    const i = line.indexOf(":");
    const head = line.slice(0, i), body = line.slice(i + 1);
    if ((body.match(/;/g) ?? []).length >= 2) body.split(";").map((x) => x.trim()).filter(Boolean).forEach((item) => out.push([n, `${head}: ${item}`]));
  });
  return out;
}

function label(head: string) {
  if (head.startsWith("ACTION")) return `Suggested action · ${head.toLowerCase().includes("your") ? "your data" : "research"}`;
  if (head.startsWith("UPLOADED")) return `Your data · ${head.replace("UPLOADED", "").split("(")[0].trim().toLowerCase()}`;
  const h = head.split("(")[0].trim().toLowerCase();
  return h.charAt(0).toUpperCase() + h.slice(1);
}

export function retrieve(facts: string, question: string): string {
  const cs = chunks(facts);
  let q = question.toLowerCase();
  for (const [k, v] of Object.entries(SYNONYMS)) if (q.includes(k)) q += " " + v;
  const docs = [...cs.map(([, c]) => grams(c)), grams(q)];
  const df = new Map<string, number>();
  docs.forEach((d) => new Set(d).forEach((w) => df.set(w, (df.get(w) ?? 0) + 1)));
  const N = docs.length;
  const vec = (d: string[]) => {
    const tf = new Map<string, number>();
    d.forEach((w) => tf.set(w, (tf.get(w) ?? 0) + 1));
    const v = new Map<string, number>();
    let norm = 0;
    tf.forEach((c, w) => { const x = (1 + Math.log(c)) * (Math.log((1 + N) / (1 + (df.get(w) ?? 0))) + 1); v.set(w, x); norm += x * x; });
    norm = Math.sqrt(norm) || 1;
    v.forEach((x, w) => v.set(w, x / norm));
    return v;
  };
  const qv = vec(docs[docs.length - 1]);
  const hasUpload = cs.some(([, c]) => c.startsWith("UPLOADED"));
  const scored = cs.map(([parent, text], i) => {
    const dv = vec(docs[i]);
    let s = 0;
    qv.forEach((x, w) => { s += x * (dv.get(w) ?? 0); });
    if (hasUpload && (text.startsWith("UPLOADED") || text.startsWith("ACTION (suggestions for your"))) s *= 1.35;
    return { parent, text, s };
  }).sort((a, b) => b.s - a.s);
  const wantsCaveats = /limit|caveat|cause|reliab|trust|accura|weak/.test(question.toLowerCase());
  const used = new Set<number>(), picked: string[] = [];
  for (const c of scored) {
    if (c.s < 0.06 || picked.length === 3) break;
    if (c.text.startsWith("CAVEATS") && !wantsCaveats) continue;
    if (used.has(c.parent)) continue;
    used.add(c.parent);
    picked.push(c.text);
  }
  if (!picked.length) return "I couldn't match that to the current results. Try asking about conversion rates, visitor types, timing, campaigns, wasted spend, audiences, attribution, display ads or limitations.";
  return picked.map((c) => {
    const i = c.indexOf(":");
    const body = c.slice(i + 1).trim();
    return `**${label(c.slice(0, i))}.** ${body.charAt(0).toUpperCase()}${body.slice(1)}`;
  }).join("\n\n");
}

export interface ChatMessage { role: "user" | "assistant"; content: string }

export async function answer(facts: string, history: ChatMessage[]): Promise<{ text: string; source: "ai" | "built-in" }> {
  try {
    const r = await fetch("/api/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ facts, messages: history.slice(-10) }),
    });
    if (r.ok) {
      const j = await r.json();
      if (j.reply) return { text: j.reply, source: "ai" };
    }
  } catch { /* offline or no API: fall through to the built-in model */ }
  return { text: retrieve(facts, history[history.length - 1].content), source: "built-in" };
}
