import { FileText } from "lucide-react";
import { useEffect, useState } from "react";
import { Badge, Container, Hero, SectionTitle } from "../components/ui";

const TITLE = "Who Gets Credit for the Sale? Recency Bias in Last-Click Attribution and the Case for Comparing Attribution Models";
const PAPERS = [
  { file: "/paper/ChannelTrace_Paper_Extended.pdf", label: "Full paper", note: "IEEE format · 8 pages · 45 references", primary: true },
  { file: "/paper/ChannelTrace_Draft_Paper.pdf", label: "Short draft", note: "IEEE format · 5 pages · first version", primary: false },
];
const SECTIONS = [
  ["I", "Introduction", "Why journeys across several channels make last-click reports unreliable, and the five research questions."],
  ["II", "Related work", "Customer journeys, data-driven and Shapley attribution, neural models, field experiments, clickstream prediction."],
  ["III", "Data", "UCI Online Shoppers, Criteo Attribution, the Google Analytics 360 sample and a Facebook Ads export."],
  ["IV", "Methods", "The seven attribution models with their equations, the known-answer simulation and the statistical tests."],
  ["V", "The ChannelTrace system", "Browser-only analysis, the fact sheet and the two-path assistant."],
  ["VI", "Results", "Recency of last-click credit, real multi-channel journeys, model accuracy, session behaviour, assistant accuracy."],
  ["VII", "Discussion", "What practitioners and researchers should take from the results, threats to validity, ethics."],
  ["VIII", "Limitations and future work", "Associations, not causes; single-store and single-network data; next steps."],
];

function usePdf(file: string) {
  const [ok, setOk] = useState<boolean>();
  useEffect(() => {
    fetch(file, { method: "HEAD" }).then((r) => setOk(r.ok && (r.headers.get("content-type") ?? "").includes("pdf"))).catch(() => setOk(false));
  }, [file]);
  return ok;
}

function PaperCard({ file, label, note, primary }: (typeof PAPERS)[number]) {
  const ok = usePdf(file);
  return (
    <div className="card flex flex-wrap items-center justify-between gap-4 p-6">
      <div className="flex items-center gap-4">
        <FileText className={primary ? "text-accent" : "text-muted"} size={32} strokeWidth={1.5} />
        <div>
          <p className="font-semibold text-ink">{label}</p>
          <p className="mt-0.5 text-sm text-muted">{note}</p>
        </div>
      </div>
      {ok ? (
        <a href={file} className={primary ? "rounded-md bg-ink px-5 py-2.5 text-sm font-semibold text-gold" : "rounded-md border border-rule px-5 py-2.5 text-sm font-semibold text-ink hover:bg-paper"}>Download PDF</a>
      ) : <Badge kind="pending">{ok === undefined ? "Checking…" : "Not available"}</Badge>}
    </div>
  );
}

export default function Paper() {
  return (
    <>
      <Hero eyebrow="Research paper" title="The paper behind ChannelTrace" lead={TITLE} />
      <Container className="pt-8">
        <div className="grid gap-4">{PAPERS.map((x) => <PaperCard key={x.file} {...x} />)}</div>
        <p className="mt-3 text-sm text-muted">Nishaad Gangal, Om Katole, Satyam Kumar and Akshat Jhanwar (Dept. of Information Technology), with Mrs. Minal Shahakar (Dept. of Computer Engineering (Regional Language)), Pimpri Chinchwad College of Engineering, Pune.</p>
        <SectionTitle code="Structure" title="What the full paper covers" />
        <div className="grid gap-4 sm:grid-cols-2">
          {SECTIONS.map(([num, t, d]) => (
            <div key={num} className="card flex gap-4 p-5">
              <span className="w-10 shrink-0 font-serif text-2xl font-semibold text-gold">{num}</span>
              <div><p className="font-semibold text-ink">{t}</p><p className="mt-1 text-sm text-muted">{d}</p></div>
            </div>
          ))}
        </div>
      </Container>
    </>
  );
}
