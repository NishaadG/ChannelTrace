"""Known-answer validation of the attribution models.

Observational data has no ground truth for attribution, so we simulate customer journeys where each
channel's causal effect is set by us, measure each channel's *true* incremental conversions by re-running
the simulation with that channel switched off (common random numbers), and compare every model's credit
share with the true share. Repeated over several random worlds with different channel roles.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src import attribution as at

CHANNELS = ["Organic Search", "Paid Search", "Social", "Email", "Display", "Direct", "Referral"]
OUT = Path(__file__).resolve().parent.parent / "data" / "processed" / "simulation_results.json"


def simulate(n_users, first_p, next_p, lift, seed, off=None, delayed=False):
    """Same seed => same random draws, so switching a channel off changes only that channel's effect."""
    rng = np.random.default_rng(seed)
    rows = []
    t0 = pd.Timestamp("2026-08-01")
    for u in range(n_users):
        u_draws = rng.random(40)  # fixed per-user uniform stream
        k = 0

        def nxt():
            nonlocal k
            k += 1
            return u_draws[k - 1]

        ch = CHANNELS[int(np.searchsorted(np.cumsum(first_p), nxt()))]
        t = t0 + pd.Timedelta(days=45 * nxt())
        logit, path = -3.0, []
        converted = False
        for step in range(8):
            path.append((t, ch))
            effect = 0.0 if ch == off else lift[ch] * 6
            if not delayed:  # immediate: a touch raises the chance of buying in the same visit
                logit += effect
            p_conv = 1 / (1 + np.exp(-logit)) * (0.25 if step == 0 else 0.45)
            if delayed:  # carry-over: a touch only raises the chance of buying on later visits
                logit += effect
            if nxt() < p_conv:
                converted = True
                break
            if nxt() < 0.35:
                break
            t = t + pd.Timedelta(hours=float(-60 * np.log(max(nxt(), 1e-9))))
            ch = CHANNELS[int(np.searchsorted(np.cumsum(next_p), nxt()))]
        for i, (tt, c) in enumerate(path):
            rows.append((u, tt, c, int(converted and i == len(path) - 1)))
    return pd.DataFrame(rows, columns=["user_id", "timestamp", "channel", "converted"])


def world(seed):
    rng = np.random.default_rng(1000 + seed)
    first_p = rng.dirichlet(np.ones(len(CHANNELS)) * 2)
    next_p = rng.dirichlet(np.ones(len(CHANNELS)) * 2)
    lift = dict(zip(CHANNELS, rng.uniform(0.01, 0.25, len(CHANNELS))))
    return first_p, next_p, lift


def run(n_worlds=6, n_users=3000, delayed=False):
    rows = []
    for w in range(n_worlds):
        first_p, next_p, lift = world(w)
        base = simulate(n_users, first_p, next_p, lift, seed=w, delayed=delayed)
        total = base.groupby("user_id")["converted"].max().sum()
        true_inc = {}
        for c in CHANNELS:
            off = simulate(n_users, first_p, next_p, lift, seed=w, off=c, delayed=delayed)
            true_inc[c] = max(0, total - off.groupby("user_id")["converted"].max().sum())
        true_share = pd.Series(true_inc) / sum(true_inc.values())
        table = at.attribute(at.build_paths(at.load(base)))
        share = (table / table.sum()).reindex(CHANNELS).fillna(0)
        for m in at.MODELS:
            err = (share[m] - true_share).abs()
            rank_corr = share[m].rank().corr(true_share.rank(), method="spearman")
            rows.append({"world": w, "model": m, "mae_pp": 100 * err.mean(), "max_err_pp": 100 * err.max(),
                         "spearman": rank_corr})
        print(f"world {w}: {total} conversions", flush=True)
    df = pd.DataFrame(rows)
    summary = (df.groupby("model").agg(mae_pp=("mae_pp", "mean"), mae_sd=("mae_pp", "std"),
                                       max_err_pp=("max_err_pp", "mean"), spearman=("spearman", "mean"))
               .reindex(at.MODELS).reset_index())
    return df, summary


def bootstrap_shares(paths: pd.DataFrame, n_boot=200, seed=0):
    """95% bootstrap intervals for each channel's credit share, resampling journeys."""
    rng = np.random.default_rng(seed)
    draws = []
    for _ in range(n_boot):
        idx = rng.integers(0, len(paths), len(paths))
        t = at.attribute(paths.iloc[idx].reset_index(drop=True))
        draws.append(t / t.sum())
    stack = np.stack([d.values for d in draws])
    lo, hi = np.percentile(stack, 2.5, axis=0), np.percentile(stack, 97.5, axis=0)
    cols, idx = draws[0].columns, draws[0].index
    return pd.DataFrame(lo, idx, cols), pd.DataFrame(hi, idx, cols)


if __name__ == "__main__":
    result = {}
    for name, delayed in [("immediate", False), ("carryover", True)]:
        df, summary = run(delayed=delayed)
        print(name); print(summary.round(3).to_string(index=False))
        result[name] = {"per_world": df.to_dict("records"), "summary": summary.to_dict("records")}
    OUT.write_text(json.dumps(result, indent=1))
    print("saved", OUT)
