import { Menu, X } from "lucide-react";
import { useEffect, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";

const LINKS = [
  { to: "/", label: "Overview" },
  { to: "/research", label: "Research" },
  { to: "/analyse", label: "Analyse your data" },
  { to: "/assistant", label: "Assistant" },
  { to: "/paper", label: "Paper" },
];

export function Mark({ className = "h-7 w-7" }: { className?: string }) {
  return (
    <svg viewBox="0 0 32 32" className={className} aria-hidden="true">
      <rect width="32" height="32" rx="7" fill="#1B2B4F" />
      <path d="M7 21 L13 13 L19 18 L25 9" stroke="#C9A227" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
      <circle cx="25" cy="9" r="2.6" fill="#C9A227" />
    </svg>
  );
}

export default function Layout() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();
  useEffect(() => { setOpen(false); window.scrollTo(0, 0); }, [pathname]);
  const link = ({ isActive }: { isActive: boolean }) =>
    `rounded-md px-3 py-2 text-sm font-medium transition-colors ${isActive ? "bg-ink-2 text-white shadow-[inset_0_-2px_0_#C9A227]" : "text-mist hover:bg-ink-2 hover:text-white"}`;
  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-30 border-b border-ink-3 bg-ink/95 backdrop-blur">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-5 sm:px-8">
          <NavLink to="/" className="flex items-center gap-2.5">
            <Mark />
            <span className="font-serif text-xl font-semibold text-white">Channel<span className="text-gold">Trace</span></span>
          </NavLink>
          <nav className="hidden items-center gap-1 md:flex">
            {LINKS.map((l) => <NavLink key={l.to} to={l.to} end={l.to === "/"} className={link}>{l.label}</NavLink>)}
          </nav>
          <button className="rounded p-2 text-white md:hidden" aria-label="Menu" onClick={() => setOpen(!open)}>{open ? <X size={20} /> : <Menu size={20} />}</button>
        </div>
        {open && (
          <nav className="flex flex-col gap-1 border-t border-ink-3 px-5 py-3 md:hidden">
            {LINKS.map((l) => <NavLink key={l.to} to={l.to} end={l.to === "/"} className={link}>{l.label}</NavLink>)}
          </nav>
        )}
      </header>
      <main className="flex-1"><Outlet /></main>
      <footer className="mt-20 bg-ink text-mist">
        <div className="mx-auto grid max-w-6xl gap-6 px-5 py-10 text-sm sm:grid-cols-3 sm:px-8">
          <div>
            <p className="font-serif text-lg font-semibold text-white">Channel<span className="text-gold">Trace</span></p>
            <p className="mt-2 text-[0.8rem] leading-relaxed">Multi-channel digital marketing attribution and conversion analysis.</p>
          </div>
          <div className="text-[0.8rem] leading-relaxed">
            <p className="eyebrow mb-2 text-gold">Project</p>
            MDM Digital Marketing Capstone · BCE27MD06<br />PCCoE, 2026–27
          </div>
          <div className="text-[0.8rem] leading-relaxed">
            <p className="eyebrow mb-2 text-gold">Data</p>
            UCI Online Shoppers · Criteo Attribution · Google Analytics 360 sample · Kaggle Facebook Ads. Results are associations, not proof of cause.
          </div>
        </div>
      </footer>
    </div>
  );
}
