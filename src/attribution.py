"""Multi-touch attribution on customer-journey data.

Input: one row per touchpoint with user_id, timestamp, channel, converted (1 on the touch that
preceded the purchase). A journey runs up to and including the first converted touch.

Models: first touch, last touch, linear, time decay, position based (40/20/40),
Markov chain removal effect (Anderl et al., 2016) and Shapley value (Shao & Li, 2011).
Every model distributes exactly the total number of conversions.
"""
from itertools import combinations
from math import factorial

import numpy as np
import pandas as pd

MODELS = ["First touch", "Last touch", "Linear", "Time decay", "Position based", "Markov chain", "Shapley value"]


def load(raw) -> pd.DataFrame:
    df = pd.read_csv(raw) if not isinstance(raw, pd.DataFrame) else raw.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    need = {"user_id", "timestamp", "channel", "converted"}
    if not need <= set(df.columns):
        raise ValueError(f"Journey file needs columns {sorted(need)}; found {list(df.columns)}")
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df["converted"] = pd.to_numeric(df["converted"], errors="coerce").fillna(0).astype(int).clip(0, 1)
    df["channel"] = df["channel"].astype(str).str.strip()
    return df.dropna(subset=["timestamp"]).sort_values(["user_id", "timestamp"])


def build_paths(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for uid, g in df.groupby("user_id", sort=False):
        hit = np.flatnonzero(g["converted"].to_numpy())
        end = hit[0] + 1 if len(hit) else len(g)
        g = g.iloc[:end]
        rows.append((uid, g["channel"].tolist(), g["timestamp"].tolist(), bool(len(hit))))
    return pd.DataFrame(rows, columns=["user_id", "path", "times", "converted"])


def _rule_based(paths: pd.DataFrame, half_life_days: float) -> dict:
    credit = {m: {} for m in MODELS[:5]}
    add = lambda m, ch, v: credit[m].__setitem__(ch, credit[m].get(ch, 0.0) + v)
    for p, t in zip(paths["path"], paths["times"]):
        n = len(p)
        add("First touch", p[0], 1)
        add("Last touch", p[-1], 1)
        for ch in p:
            add("Linear", ch, 1 / n)
        age = np.array([(t[-1] - x).total_seconds() / 86400 for x in t])
        w = 0.5 ** (age / half_life_days)
        for ch, wi in zip(p, w / w.sum()):
            add("Time decay", ch, wi)
        if n == 1:
            pos = [1.0]
        elif n == 2:
            pos = [0.5, 0.5]
        else:
            pos = [0.4] + [0.2 / (n - 2)] * (n - 2) + [0.4]
        for ch, wi in zip(p, pos):
            add("Position based", ch, wi)
    return credit


def _markov_conv_prob(paths: pd.DataFrame, channels: list, removed: str | None = None) -> float:
    states = ["start"] + channels
    idx = {s: i for i, s in enumerate(states)}
    n = len(states)
    trans = np.zeros((n, n + 2))  # last two columns: conversion, null
    for p, conv in zip(paths["path"], paths["converted"]):
        seq = ["start"] + p
        for a, b in zip(seq[:-1], seq[1:]):
            trans[idx[a], idx[b]] += 1
        trans[idx[seq[-1]], n if conv else n + 1] += 1
    if removed is not None:
        r = idx[removed]
        trans[r, :] = 0
        trans[r, n + 1] = 1  # a removed channel leads nowhere
    rowsum = trans.sum(axis=1, keepdims=True)
    P = np.divide(trans, rowsum, out=np.zeros_like(trans), where=rowsum > 0)
    Q, R = P[:, :n], P[:, n:]
    absorb = np.linalg.solve(np.eye(n) - Q, R)
    return absorb[0, 0]


def _markov(paths: pd.DataFrame, channels: list, total: float) -> dict:
    base = _markov_conv_prob(paths, channels)
    effect = {c: max(0.0, 1 - _markov_conv_prob(paths, channels, c) / base) if base > 0 else 0 for c in channels}
    s = sum(effect.values())
    return {c: total * e / s if s else 0 for c, e in effect.items()}


def _shapley(paths: pd.DataFrame, channels: list) -> dict:
    """Coalition value v(S) = conversions from journeys whose channel set is a subset of S."""
    conv = paths[paths["converted"]]
    sets = conv["path"].map(frozenset).value_counts()
    n = len(channels)
    if n > 12:
        raise ValueError("Shapley value is limited to 12 channels")
    cache = {}

    def v(S):
        if S not in cache:
            cache[S] = sum(cnt for k, cnt in sets.items() if k <= S)
        return cache[S]

    phi = {}
    for c in channels:
        others = [x for x in channels if x != c]
        total = 0.0
        for k in range(n):
            wt = factorial(k) * factorial(n - k - 1) / factorial(n)
            for S in combinations(others, k):
                S = frozenset(S)
                total += wt * (v(S | {c}) - v(S))
        phi[c] = total
    return phi


def attribute(paths: pd.DataFrame, half_life_days: float = 7.0) -> pd.DataFrame:
    """Returns a channel x model table of attributed conversions."""
    conv = paths[paths["converted"]]
    channels = sorted({c for p in paths["path"] for c in p})
    total = float(len(conv))
    credit = _rule_based(conv, half_life_days)
    credit["Markov chain"] = _markov(paths, channels, total)
    credit["Shapley value"] = _shapley(paths, channels)
    table = pd.DataFrame(credit).reindex(channels).fillna(0.0)[MODELS]
    return table


def journey_stats(paths: pd.DataFrame) -> dict:
    conv = paths[paths["converted"]]
    top = conv["path"].map(lambda p: " > ".join(p)).value_counts().head(10)
    return {
        "journeys": len(paths),
        "conversions": len(conv),
        "conv_rate": len(conv) / len(paths) if len(paths) else 0,
        "avg_len_conv": conv["path"].map(len).mean(),
        "avg_len_nonconv": paths.loc[~paths["converted"], "path"].map(len).mean(),
        "single_touch_share": (conv["path"].map(len) == 1).mean(),
        "top_paths": top,
    }


def fact_sheet(table: pd.DataFrame, st: dict) -> str:
    share = table / table.sum()
    last, markov = share["Last touch"], share["Markov chain"]
    diff = (markov - last).sort_values()
    lines = [
        f"UPLOADED JOURNEYS: {st['journeys']:,} customer journeys, {st['conversions']:,} conversions "
        f"({st['conv_rate']:.1%}). Converting journeys average {st['avg_len_conv']:.1f} touchpoints vs "
        f"{st['avg_len_nonconv']:.1f} for non-converting; {st['single_touch_share']:.0%} of conversions had a single touch.",
        "UPLOADED TOP PATHS: " + "; ".join(f"{p} ({n})" for p, n in st["top_paths"].head(5).items()) + ".",
        "UPLOADED ATTRIBUTION SHARES (last touch / linear / Markov / Shapley): " + "; ".join(
            f"{c}: {last[c]:.0%} / {share.loc[c, 'Linear']:.0%} / {markov[c]:.0%} / {share.loc[c, 'Shapley value']:.0%}"
            for c in share.sort_values("Markov chain", ascending=False).index) + ".",
        f"UPLOADED LAST-CLICK BIAS: last-click most under-credits {diff.index[-1]} (Markov {markov[diff.index[-1]]:.0%} vs "
        f"last touch {last[diff.index[-1]]:.0%}) and most over-credits {diff.index[0]} (Markov {markov[diff.index[0]]:.0%} vs "
        f"last touch {last[diff.index[0]]:.0%}).",
        f"ACTION (suggestions for your channels): do not cut {diff.index[-1]} based on last-click reports alone, "
        f"because it contributes more to journeys than last-click shows; treat {diff.index[0]}'s last-click numbers "
        "with caution, as it often closes journeys that other channels started. Compare models before moving budget.",
    ]
    return "\n".join(lines)
