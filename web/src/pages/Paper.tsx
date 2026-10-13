import { FileText } from "lucide-react";
import { useEffect, useState } from "react";
import { Badge, Container, Hero, SectionTitle } from "../components/ui";

const SECTIONS = [
  ["1", "Introduction", "Why multi-channel journeys make last-click measurement unreliable."],
  ["2", "Related work", "Rule-based and data-driven attribution; predicting purchase from sessions."],
  ["3", "Data", "UCI Online Shoppers, Criteo Attribution, Google Analytics 360 sample, Kaggle Facebook Ads."],
  ["4", "Methods", "Seven attribution models, statistical tests, classifiers and the known-answer simulation."],
  ["5", "Results", "Session behaviour, the last-click recency effect, model accuracy under two scenarios."],
  ["6", "The ChannelTrace tool", "Plug-and-play analysis and a grounded AI assistant, at zero cost."],
  ["7", "Discussion and limitations", "Associations, not causes; obfuscated and single-channel data."],
];

export default function Paper() {
  const [available, setAvailable] = useState<boolean>();
  useEffect(() => { fetch("/paper/ChannelTrace_Draft_Paper.pdf", { method: "HEAD" }).then((r) => setAvailable(r.ok && (r.headers.get("content-type") ?? "").includes("pdf"))).catch(() => setAvailable(false)); }, []);
  return (
    <>
      <Hero eyebrow="Research paper" title="Draft paper"
        lead="The study behind ChannelTrace, written up as a research paper with original results." />
      <Container className="pt-8">
        <div className="card flex flex-wrap items-center justify-between gap-4 p-6">
          <div className="flex items-center gap-4">
            <FileText className="text-accent" size={32} strokeWidth={1.5} />
            <div>
              <p className="font-semibold text-ink">Last-Click Rewards Recency: A Multi-Dataset Study of Digital Marketing Attribution</p>
              <p className="mt-0.5 text-sm text-muted">Draft for review · 2026</p>
            </div>
          </div>
          {available ? (
            <a href="/paper/ChannelTrace_Draft_Paper.pdf" className="rounded-md bg-ink px-5 py-2.5 text-sm font-semibold text-gold">Download PDF</a>
          ) : <Badge kind="pending">{available === undefined ? "Checking…" : "Draft in preparation"}</Badge>}
        </div>
        <SectionTitle code="Structure" title="What the paper covers" />
        <div className="grid gap-4 sm:grid-cols-2">
          {SECTIONS.map(([n, t, d]) => (
            <div key={n} className="card flex gap-4 p-5">
              <span className="font-serif text-2xl font-semibold text-gold">{n}</span>
              <div><p className="font-semibold text-ink">{t}</p><p className="mt-1 text-sm text-muted">{d}</p></div>
            </div>
          ))}
        </div>
      </Container>
    </>
  );
}
