import { ArrowRight } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { Container, Finding, Hero, Note, SectionTitle, Table } from "../components/ui";
import { MODELS, attribute, type Journey } from "../lib/attribution";

const DAY = 86400000;
// Example journeys: channel and days before the purchase (the last touch is the one that ends in the sale)
const EXAMPLES: { name: string; touches: [string, number][] }[] = [
  { name: "Instagram ad, then search, then email", touches: [["Social", 12], ["Paid Search", 4], ["Email", 0]] },
  { name: "Display ad, buys three weeks later", touches: [["Display", 21], ["Direct", 0]] },
  { name: "Long journey with a repeat channel", touches: [["Organic Search", 9], ["Social", 6], ["Organic Search", 2], ["Referral", 0]] },
];

const PLAIN: [string, string, string][] = [
  ["First touch", "All credit to the channel that first brought the customer in.", "Worst in both of our simulated scenarios; it ignores everything after discovery."],
  ["Last touch", "All credit to the final interaction before the sale. The default in most ad reports.", "Close to the truth when ads trigger sales on the spot; poor when their effect builds up over later visits."],
  ["Linear", "Every touch gets an equal share.", "Among the most accurate when effects carry over, because it does not bet on one end of the journey."],
  ["Time decay", "Recent touches count more; a touch loses half its weight for every 7 days before the sale.", "Near the top in both scenarios. A safe default when you do not know how your ads work."],
  ["Position based", "40% to the first touch, 40% to the last, 20% shared by the ones in between.", "A compromise between first and last touch; middling accuracy in our tests."],
  ["Markov chain", "Treats journeys as steps between channels and asks how many sales would be lost if a channel were removed. Uses buyers and non-buyers.", "Recovered designed channel roles well, but was never the most accurate in our simulation."],
  ["Shapley value", "From game theory: each channel's average extra contribution over every possible combination of channels.", "Ranked channels in the right order almost as well as the best model in both scenarios."],
];

export default function Method() {
  const [ex, setEx] = useState(0);
  const journey: Journey = useMemo(() => {
    const t = EXAMPLES[ex].touches;
    return { user: "example", path: t.map(([c]) => c), times: t.map(([, d]) => Date.UTC(2026, 0, 30) - d * DAY), converted: true };
  }, [ex]);
  const table = useMemo(() => attribute([journey]), [journey]);
  const chans = [...new Set(journey.path)];
  return (
    <>
      <Hero eyebrow="How it works" title="How ChannelTrace decides who gets credit"
        lead="One sale, several channels, seven ways of splitting the credit. This page shows what each attribution model does with a real-looking journey, and what happens to your file when you upload it." />
      <Container className="pt-8">
        <SectionTitle code="Try it" title="One journey, seven answers" />
        <div className="mb-4 flex flex-wrap gap-2" role="radiogroup" aria-label="Example journey">
          {EXAMPLES.map((e, i) => (
            <button key={e.name} role="radio" aria-checked={ex === i} onClick={() => setEx(i)}
              className={`rounded-md border px-3.5 py-2 text-sm font-medium ${ex === i ? "border-accent bg-accent-soft text-ink" : "border-rule text-muted hover:text-ink"}`}>
              {e.name}
            </button>
          ))}
        </div>
        <div className="card mb-5 flex flex-wrap items-center gap-2 p-4 text-sm">
          {EXAMPLES[ex].touches.map(([c, d], i) => (
            <span key={i} className="flex items-center gap-2">
              <span className="rounded border border-rule bg-paper px-2.5 py-1"><b className="text-ink">{c}</b> <span className="text-muted">· {d ? `${d} day${d > 1 ? "s" : ""} before` : "day of sale"}</span></span>
              <ArrowRight size={14} className="text-muted" />
            </span>
          ))}
          <span className="rounded bg-ink px-2.5 py-1 font-semibold text-gold">Purchase</span>
        </div>
        <Table head={["Model", ...chans]} numeric={chans.map((_, i) => i + 1)}
          rows={MODELS.map((m) => [m, ...chans.map((c) => `${Math.round((table[c]?.[m] ?? 0) * 100)}%`)])} />
        <Note>Share of the one sale given to each channel. With a single journey, the Markov and Shapley models can only split the credit evenly between the channels used: they learn from many journeys, including people who did not buy, which is what the upload tool gives them.</Note>
        <Finding label="Why this matters">
          The same sale can make a channel look essential or useless depending on the rule. In our known-answer simulation no single model was best: last touch was right when ads work immediately, time decay and linear when their effect builds up. ChannelTrace therefore always shows all seven side by side, and a channel whose credit swings a lot between them should be treated as uncertain. <Link to="/research" className="font-medium text-accent underline">See the validation results</Link>.
        </Finding>

        <SectionTitle code="The models" title="Seven models in plain language" />
        <div className="grid gap-4 md:grid-cols-2">
          {PLAIN.map(([m, rule, verdict]) => (
            <div key={m} className="card p-5">
              <p className="font-semibold text-ink">{m}</p>
              <p className="mt-1.5 text-sm leading-relaxed text-text">{rule}</p>
              <p className="mt-2 text-[0.8rem] leading-relaxed text-muted"><span className="font-semibold text-accent">In our tests:</span> {verdict}</p>
            </div>
          ))}
        </div>

        <SectionTitle code="Privacy" title="What happens to your file" />
        <div className="grid items-start gap-6 lg:grid-cols-5">
          <figure className="card p-4 lg:col-span-2">
            <img src="/method/architecture.png" alt="Diagram: the uploaded CSV is parsed, analysed and summarised in the browser; only the summary fact sheet goes to the assistant" className="w-full" />
            <figcaption className="mt-2 text-[0.78rem] text-muted">Everything inside the dashed box runs in your browser.</figcaption>
          </figure>
          <ol className="list-decimal space-y-3 pl-5 text-sm leading-relaxed text-text lg:col-span-3">
            <li><b className="text-ink">Read in the browser.</b> Your CSV is parsed on your own computer. It is never uploaded to a server.</li>
            <li><b className="text-ink">Recognised and cleaned.</b> Google Ads, Meta Ads Manager and journey exports are detected from their column names, which are mapped to one format.</li>
            <li><b className="text-ink">Analysed.</b> Ad files get CTR, CPC, CPA and ROAS per campaign, a verdict against the account average and the spend that produced nothing. Journey files go through all seven models.</li>
            <li><b className="text-ink">Summarised.</b> The results become a short fact sheet of computed figures. That sheet, and nothing else, is what the assistant sees.</li>
            <li><b className="text-ink">Explained.</b> The assistant answers from the fact sheet, using a free Gemini model when available and a built-in search over the sheet otherwise. It is told to say when the data cannot answer a question.</li>
          </ol>
        </div>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link to="/analyse" className="inline-flex items-center gap-2 rounded-md bg-ink px-5 py-2.5 text-sm font-semibold text-gold">Try it on your data <ArrowRight size={16} /></Link>
          <Link to="/paper" className="inline-flex items-center gap-2 rounded-md border border-rule px-5 py-2.5 text-sm font-semibold text-ink hover:bg-paper">Read the paper</Link>
        </div>
      </Container>
    </>
  );
}
