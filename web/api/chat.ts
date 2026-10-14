// Vercel serverless function: generative answers via Google Gemini's free tier when GEMINI_API_KEY is set.
// Without a key it returns 503 and the site falls back to its built-in retrieval model.
export const config = { runtime: "edge" };

const SYSTEM = `You are ChannelTrace's marketing analytics assistant for small businesses and students.
Answer ONLY from the FACTS below. If the facts do not cover a question, say so and suggest what data would answer it.
Use plain language, short paragraphs and concrete numbers from the facts. Mark recommendations as suggestions and
remind that the data shows associations, not proof of cause. Keep answers under 180 words.

FACTS:
`;

const API = "https://generativelanguage.googleapis.com/v1beta";
let candidates: string[] | undefined; // remembered while the function instance stays warm

// Model names get retired and the free tier is often overloaded, so try the latest Flash alias, then the
// lighter Flash-Lite models (usually less busy), then the other Flash models this key can use.
async function flashModels(key: string): Promise<string[]> {
  const res = await fetch(`${API}/models?pageSize=200&key=${key}`);
  if (!res.ok) return [];
  const { models = [] } = (await res.json()) as { models?: { name: string; supportedGenerationMethods?: string[] }[] };
  const names = models
    .filter((m) => m.supportedGenerationMethods?.includes("generateContent"))
    .map((m) => m.name.replace(/^models\//, ""));
  const version = (n: string) => parseFloat(n.split("-")[1]);
  const pick = (re: RegExp) => names.filter((n) => re.test(n)).sort((x, y) => version(y) - version(x));
  return [...new Set(["gemini-flash-latest", "gemini-flash-lite-latest", ...pick(/^gemini-[\d.]+-flash-lite$/), ...pick(/^gemini-[\d.]+-flash$/)])];
}

export default async function handler(req: Request): Promise<Response> {
  if (req.method !== "POST") return new Response("Method not allowed", { status: 405 });
  const key = process.env.GEMINI_API_KEY;
  if (!key) return Response.json({ error: "no_key" }, { status: 503 });
  let body: { facts?: string; messages?: { role: string; content: string }[] };
  try {
    body = await req.json();
  } catch {
    return Response.json({ error: "bad_json" }, { status: 400 });
  }
  const facts = String(body.facts ?? "").slice(0, 20000);
  const messages = (body.messages ?? []).slice(-10).map((m) => ({
    role: m.role === "assistant" ? "model" : "user",
    parts: [{ text: String(m.content).slice(0, 2000) }],
  }));
  const ask = (model: string) =>
    fetch(`${API}/models/${model}:generateContent?key=${key}`, {
      method: "POST",
      signal: AbortSignal.timeout(9000),
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        systemInstruction: { parts: [{ text: SYSTEM + facts }] },
        contents: messages,
        generationConfig: { temperature: 0.3 },
      }),
    });
  candidates ??= [process.env.GEMINI_MODEL ?? "", ...(await flashModels(key))].filter(Boolean);
  let r: Response | undefined;
  let used = "";
  const tried: string[] = [];
  const started = Date.now();
  for (const model of candidates) {
    if (Date.now() - started > 18000) break; // stay inside the edge function's time limit
    used = model;
    r = await ask(model).catch(() => undefined);
    tried.push(`${model}:${r?.status ?? "timeout"}`);
    if (r && ![404, 429, 500, 503].includes(r.status)) break;
  }
  if (!r?.ok) return Response.json({ error: "upstream", tried }, { status: 502 });
  const j = await r.json();
  const reply = j?.candidates?.[0]?.content?.parts?.map((p: { text?: string }) => p.text ?? "").join("") ?? "";
  return Response.json({ reply, model: used });
}
