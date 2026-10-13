import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export interface Research {
  uci: {
    sessions: number; conversion_rate: number; purchases: number;
    visitor: { VisitorType: string; sessions: number; conversions: number; conversion_rate: number }[];
    month: { Month: string; sessions: number; conversion_rate: number }[];
    traffic: { TrafficType: number; sessions: number; conversion_rate: number }[];
    weekend: { Weekend: boolean; conversion_rate: number }[];
    groups: Record<string, number | string | boolean>[];
    models: Record<"with_page_values" | "without_page_values", { logit_auc: number; rf_auc: number; hgb_auc: number; importance: { feature: string; importance: number }[] }>;
  };
  criteo: {
    impressions: number; users: number; campaigns: number; clicks: number; conversions: number;
    single_campaign_share: number; touches_mean: number; touches_p90: number; single_touch_share: number;
    attributed_share: number; hours_last_to_conv_median: number; span_days_median_multi: number;
    attributed_by_touches: Record<string, { share: number; n: number }>;
    attributed_by_hours_since_last_click: Record<string, { share: number; n: number }>;
    touches_hist: Record<string, number>;
  };
  simulation: Record<"immediate" | "carryover", { summary: { model: string; mae_pp: number; mae_sd: number; max_err_pp: number; spearman: number }[] }>;
  synthetic_bootstrap: Record<string, Record<string, [number, number, number]>>;
  ga360?: Record<string, unknown>;
  facts: string;
}

interface Ctx {
  research?: Research;
  dataFacts: Record<string, string>;
  setDataFact: (k: string, v: string | null) => void;
}
const DataCtx = createContext<Ctx>({ dataFacts: {}, setDataFact: () => {} });

export function DataProvider({ children }: { children: ReactNode }) {
  const [research, setResearch] = useState<Research>();
  const [dataFacts, setFacts] = useState<Record<string, string>>(() => {
    try { return JSON.parse(sessionStorage.getItem("ct-facts") ?? "{}"); } catch { return {}; }
  });
  useEffect(() => { fetch("/data/research.json").then((r) => r.json()).then(setResearch).catch(() => {}); }, []);
  const setDataFact = (k: string, v: string | null) => setFacts((prev) => {
    const next = { ...prev };
    if (v === null) delete next[k]; else next[k] = v;
    try { sessionStorage.setItem("ct-facts", JSON.stringify(next)); } catch { /* storage unavailable */ }
    return next;
  });
  return <DataCtx.Provider value={{ research, dataFacts, setDataFact }}>{children}</DataCtx.Provider>;
}

export const useData = () => useContext(DataCtx);

export function Loading() {
  return <div className="mx-auto max-w-6xl px-8 py-24 text-center text-sm text-muted">Loading results…</div>;
}
