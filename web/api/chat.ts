// Vercel serverless function: generative answers via Google Gemini's free tier when GEMINI_API_KEY is set.
// Without a key it returns 503 and the site falls back to its built-in retrieval model.
export const config = { runtime: "edge" };

const SYSTEM = `You are ChannelTrace's marketing analytics assistant for small businesses and students.
Answer ONLY from the FACTS below. If the facts do not cover a question, say so and suggest what data would answer it.
Use plain language, short paragraphs and concrete numbers from the facts. Mark recommendations as suggestions and
remind that the data shows associations, not proof of cause. Keep answers under 180 words.

FACTS:
`;

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
  const model = process.env.GEMINI_MODEL || "gemini-2.5-flash";
  const r = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/${model}:generateContent?key=${key}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      systemInstruction: { parts: [{ text: SYSTEM + facts }] },
      contents: messages,
      generationConfig: { temperature: 0.3 },
    }),
  });
  if (!r.ok) return Response.json({ error: "upstream", status: r.status }, { status: 502 });
  const j = await r.json();
  const reply = j?.candidates?.[0]?.content?.parts?.map((p: { text?: string }) => p.text ?? "").join("") ?? "";
  return Response.json({ reply });
}
