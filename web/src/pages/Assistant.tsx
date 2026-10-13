import { Bot, RotateCcw, Send, User } from "lucide-react";
import { useEffect, useRef, useState, type ReactNode } from "react";
import { Badge, Container, Hero } from "../components/ui";
import { useData } from "../data";
import { answer, type ChatMessage } from "../lib/assistant";

function Md({ text }: { text: string }) {
  // minimal markdown: paragraphs and **bold**
  return (
    <div className="prose-answer space-y-2.5 text-[0.93rem] leading-relaxed">
      {text.split(/\n{2,}/).map((para, i) => (
        <p key={i}>{para.split(/(\*\*[^*]+\*\*)/g).map((seg, j): ReactNode => (seg.startsWith("**") ? <strong key={j}>{seg.slice(2, -2)}</strong> : seg))}</p>
      ))}
    </div>
  );
}

export default function Assistant() {
  const { research, dataFacts } = useData();
  const [chat, setChat] = useState<(ChatMessage & { source?: string })[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState<"ai" | "built-in">();
  const end = useRef<HTMLDivElement>(null);
  const facts = [research?.facts ?? "", ...Object.values(dataFacts)].join("\n");
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [chat, busy]);

  let suggestions = ["Summarise the key research findings", "Why does last-click give the wrong answer?", "Which attribution model is most accurate?", "How can a store convert more returning visitors?"];
  if (dataFacts.ads) suggestions = ["Which campaigns should I cut or scale?", "Where is money being wasted?", "Which audience converts most cheaply?", suggestions[1]];
  if (dataFacts.journeys) suggestions = ["Which channel does last-click undervalue?", "What are the most common paths to purchase?", ...suggestions.slice(0, 2)];

  const ask = async (q: string) => {
    if (!q.trim() || busy) return;
    const history = [...chat, { role: "user" as const, content: q.trim() }];
    setChat(history); setDraft(""); setBusy(true);
    const r = await answer(facts, history);
    setMode(r.source);
    setChat([...history, { role: "assistant", content: r.text, source: r.source }]);
    setBusy(false);
  };

  return (
    <>
      <Hero eyebrow="Marketing assistant" title="Ask the data"
        lead="Answers come only from ChannelTrace's computed results: the research findings and any file you analyse. Raw rows never leave your browser, and every recommendation is a suggestion, not a guarantee." />
      <Container className="pt-8">
        <div className="mb-4 flex flex-wrap gap-2">
          <Badge kind={mode === "ai" ? "good" : "info"}>{mode === "ai" ? "Generative AI (Gemini free tier)" : "Built-in retrieval model"}</Badge>
          <Badge>Research findings loaded</Badge>
          {dataFacts.ads && <Badge kind="good">Your ad data loaded</Badge>}
          {dataFacts.journeys && <Badge kind="good">Your journey data loaded</Badge>}
        </div>
        <div className="card flex min-h-[460px] flex-col">
          <div className="flex-1 space-y-4 p-5 sm:p-6">
            {!chat.length && (
              <div className="py-6">
                <p className="text-sm text-muted">Start with a question, or pick one:</p>
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  {suggestions.map((s) => (
                    <button key={s} onClick={() => ask(s)} className="rounded-md border border-rule px-4 py-3 text-left text-sm text-ink transition-colors hover:border-accent hover:text-accent">{s}</button>
                  ))}
                </div>
              </div>
            )}
            {chat.map((m, i) => (
              <div key={i} className={`fade-in flex gap-3 ${m.role === "user" ? "justify-end" : ""}`}>
                {m.role === "assistant" && <span className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-ink text-gold"><Bot size={16} /></span>}
                <div className={`max-w-[85%] rounded-lg px-4 py-3 ${m.role === "user" ? "bg-ink text-white" : "border border-rule bg-paper"}`}>
                  {m.role === "user" ? <p className="text-[0.93rem]">{m.content}</p> : <Md text={m.content} />}
                </div>
                {m.role === "user" && <span className="mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent-soft text-accent"><User size={16} /></span>}
              </div>
            ))}
            {busy && <p className="pl-11 text-sm text-muted">Reading the results…</p>}
            <div ref={end} />
          </div>
          <form onSubmit={(e) => { e.preventDefault(); ask(draft); }} className="flex items-center gap-2 border-t border-rule p-3">
            {chat.length > 0 && <button type="button" title="Clear conversation" onClick={() => setChat([])} className="rounded-md p-2 text-muted hover:text-ink"><RotateCcw size={18} /></button>}
            <input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Ask about campaigns, channels, audiences, timing or methods"
              className="flex-1 rounded-md border border-rule bg-paper px-4 py-2.5 text-sm outline-none focus:border-accent" />
            <button disabled={busy || !draft.trim()} className="rounded-md bg-ink p-2.5 text-gold disabled:opacity-40" aria-label="Send"><Send size={18} /></button>
          </form>
        </div>
        <details className="mt-4 text-[0.8rem] text-muted">
          <summary className="cursor-pointer">What the assistant knows</summary>
          <pre className="card mt-2 max-h-80 overflow-auto whitespace-pre-wrap p-4 font-mono text-[0.75rem]">{facts}</pre>
        </details>
      </Container>
    </>
  );
}
