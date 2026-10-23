import { ArrowRight, BarChart3, Bot, FlaskConical } from "lucide-react";
import { Link } from "react-router-dom";
import { Badge, Container, Hero, SectionTitle, Table } from "../components/ui";
import { useData } from "../data";

const pct = (x?: number, d = 0) => (x === undefined ? "–" : `${(x * 100).toFixed(d)}%`);

export default function Home() {
  const { research: r } = useData();
  const cr = r?.criteo;
  return (
    <>
      <Hero eyebrow="Capstone research · MDM Digital Marketing · 2026–27" title={<>Which channels really lead to a sale?</>}
        lead="Customers rarely buy after one ad. They find a brand through search, return through social, open an email and only then purchase. ChannelTrace measures how much credit each channel deserves, shows how much that answer depends on the attribution rule, and turns it into advice a small business can act on.">
        <div className="mt-8 flex flex-wrap gap-3">
          <Link to="/analyse" className="inline-flex items-center gap-2 rounded-md bg-gold px-5 py-2.5 text-sm font-semibold text-ink hover:brightness-105">Analyse your ad data <ArrowRight size={16} /></Link>
          <Link to="/research" className="inline-flex items-center gap-2 rounded-md border border-ink-3 px-5 py-2.5 text-sm font-semibold text-white hover:bg-ink-2">Read the findings</Link>
        </div>
        <div className="mt-12 grid gap-px overflow-hidden rounded-lg border border-ink-3 bg-ink-3 sm:grid-cols-3">
          {[
            [pct(cr?.attributed_share), "of conversions after a Criteo click were credited to Criteo by last-click; the rest went to other channels"],
            [cr ? `${pct(cr.attributed_by_hours_since_last_click["<1h"].share)} → ${pct(cr.attributed_by_hours_since_last_click["7-31d"].share)}` : "–", "last-click credit within an hour vs after 7–31 days: recency, not contribution, decides credit"],
            ["No winner", "in a known-answer simulation, the most accurate attribution model changes with how ads actually work"],
          ].map(([v, t]) => (
            <div key={t} className="bg-ink p-6">
              <p className="font-serif text-3xl font-semibold text-white">{v}</p>
              <p className="mt-2 text-[0.85rem] leading-relaxed text-mist">{t}</p>
            </div>
          ))}
        </div>
      </Hero>

      <Container>
        <SectionTitle code="What it is" title="Research, a working tool and an assistant" />
        <div className="grid gap-5 md:grid-cols-3">
          {[
            { icon: FlaskConical, title: "Research findings", to: "/research", body: "Four public datasets, seven attribution models, conversion modelling and a known-answer validation study." },
            { icon: BarChart3, title: "Analyse your data", to: "/analyse", body: "Drop in a Google Ads, Meta Ads or customer-journey CSV. It is analysed in your browser and never uploaded." },
            { icon: Bot, title: "Marketing assistant", to: "/assistant", body: "Plain-language answers and suggested actions, grounded only in the computed results." },
          ].map(({ icon: Icon, title, body, to }) => (
            <Link key={title} to={to} className="card group p-6 transition-shadow hover:shadow-[0_6px_24px_rgba(20,33,61,0.08)]">
              <Icon className="text-accent" size={26} strokeWidth={1.75} />
              <h3 className="mt-4 font-sans text-lg font-semibold">{title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-muted">{body}</p>
              <span className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-accent">Open <ArrowRight size={14} className="transition-transform group-hover:translate-x-0.5" /></span>
            </Link>
          ))}
        </div>

        <SectionTitle code="Scope" title="Research questions" />
        <Table head={["", "Question", "Evidence", "Status"]} rows={[
          ["RQ1", "What channel journeys commonly come before a conversion?", "Google Analytics 360 sample", <Badge kind={r?.ga360 ? "good" : "pending"}>{r?.ga360 ? "Answered" : "Data access pending"}</Badge>],
          ["RQ2", "How do converting and non-converting sessions differ?", "UCI Online Shoppers", <Badge kind="good">Answered</Badge>],
          ["RQ3", "Does a channel's importance change under different attribution models?", "Criteo, simulation, GA360", <Badge kind="good">Answered</Badge>],
          ["RQ4", "Which visitor and session traits are associated with conversion?", "UCI Online Shoppers", <Badge kind="good">Answered</Badge>],
          ["RQ5", "Can the methods give small businesses correct, usable insight from their own data?", "Facebook Ads data, assistant test", <Badge kind={r?.assistant_eval ? "good" : "pending"}>{r?.assistant_eval ? "Answered" : "Tool built · test pending"}</Badge>],
        ].map(([c, ...rest]) => [<span className="font-semibold text-accent">{c}</span>, ...rest])} />

        <SectionTitle code="Evidence" title="Data sources" />
        <Table head={["Dataset", "Size", "Used for"]} rows={[
          ["UCI Online Shoppers Purchasing Intention", "12,330 sessions", "Behaviour associated with purchase (RQ2, RQ4)"],
          ["Criteo Attribution Modeling for Bidding", "16.5M impressions, 675 campaigns", "Last-click gap, recency of credit (RQ3)"],
          ["Google Analytics 360 sample (Merchandise Store)", "12 months of sessions", "Multi-session channel journeys (RQ1, RQ3)"],
          ["Facebook Ad Campaign (Kaggle)", "1,143 ads", "Validating the upload tool on real data (RQ5)"],
          ["Assistant test set (ours)", r?.assistant_eval ? `${r.assistant_eval.n} questions` : "Fixed questions", "Accuracy of the assistant's answers (RQ5)"],
        ]} />
      </Container>
    </>
  );
}
