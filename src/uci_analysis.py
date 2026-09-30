"""Research analysis on the UCI Online Shoppers Purchasing Intention dataset (RQ2, RQ4).

Source: Sakar, C. O. and Kastro, Y. (2018). UCI ML Repository, Dataset 468.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, mannwhitneyu
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

DATA = Path(__file__).resolve().parent.parent / "data" / "raw" / "online_shoppers_intention.csv"
MONTH_ORDER = ["Feb", "Mar", "May", "June", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
NUMERIC = [
    "Administrative", "Administrative_Duration", "Informational", "Informational_Duration",
    "ProductRelated", "ProductRelated_Duration", "BounceRates", "ExitRates", "PageValues", "SpecialDay",
]
READABLE = {
    "Administrative": "Account/admin pages viewed",
    "Administrative_Duration": "Time on account pages (s)",
    "Informational": "Info pages viewed",
    "Informational_Duration": "Time on info pages (s)",
    "ProductRelated": "Product pages viewed",
    "ProductRelated_Duration": "Time on product pages (s)",
    "BounceRates": "Bounce rate",
    "ExitRates": "Exit rate",
    "PageValues": "Page value",
    "SpecialDay": "Closeness to a special day",
    "Weekend": "Weekend visit",
    "VisitorType_New_Visitor": "New visitor",
    "VisitorType_Returning_Visitor": "Returning visitor",
    "VisitorType_Other": "Other visitor type",
}


def load() -> pd.DataFrame:
    df = pd.read_csv(DATA)
    df = df.drop_duplicates()
    df["Revenue"] = df["Revenue"].astype(bool)
    df["Weekend"] = df["Weekend"].astype(bool)
    return df


def rate_by(df: pd.DataFrame, col: str, min_sessions: int = 0) -> pd.DataFrame:
    out = (df.groupby(col)["Revenue"].agg(sessions="size", conversions="sum").reset_index())
    out["conversion_rate"] = out["conversions"] / out["sessions"]
    return out[out["sessions"] >= min_sessions]


def compare_groups(df: pd.DataFrame) -> pd.DataFrame:
    """RQ2: converting vs non-converting sessions, medians + Mann-Whitney U."""
    rows = []
    buy, no = df[df["Revenue"]], df[~df["Revenue"]]
    for c in NUMERIC:
        p = mannwhitneyu(buy[c], no[c]).pvalue
        rows.append({
            "Behaviour": READABLE[c],
            "Median (converted)": buy[c].median(),
            "Median (not converted)": no[c].median(),
            "Mean (converted)": buy[c].mean(),
            "Mean (not converted)": no[c].mean(),
            "p-value": p,
            "Significant (p<0.05)": p < 0.05,
        })
    return pd.DataFrame(rows)


def chi_square(df: pd.DataFrame, col: str) -> float:
    return chi2_contingency(pd.crosstab(df[col], df["Revenue"]))[1]


def _features(df: pd.DataFrame, with_page_values: bool) -> pd.DataFrame:
    cols = NUMERIC if with_page_values else [c for c in NUMERIC if c != "PageValues"]
    X = df[cols + ["Weekend"]].astype(float)
    X = X.join(pd.get_dummies(df["VisitorType"], prefix="VisitorType", dtype=float))
    X = X.join(pd.get_dummies(df["Month"], prefix="Month", dtype=float))
    return X


def model_results(df: pd.DataFrame, seed: int = 42) -> dict:
    """RQ4: logistic regression + random forest, with and without PageValues.

    PageValues is derived from pages that preceded transactions, so it partly leaks the
    outcome; reporting both versions shows how much the model leans on it.
    """
    y = df["Revenue"].astype(int)
    results = {}
    for with_pv in (True, False):
        X = _features(df, with_pv)
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, stratify=y, random_state=seed)
        logit = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, class_weight="balanced"))
        logit.fit(Xtr, ytr)
        rf = RandomForestClassifier(n_estimators=300, min_samples_leaf=5, class_weight="balanced",
                                    random_state=seed, n_jobs=-1)
        rf.fit(Xtr, ytr)
        imp = permutation_importance(rf, Xte, yte, scoring="roc_auc", n_repeats=5, random_state=seed, n_jobs=-1)
        importance = (pd.DataFrame({"feature": X.columns, "importance": imp.importances_mean})
                      .sort_values("importance", ascending=False))
        importance["feature"] = importance["feature"].map(lambda f: READABLE.get(f, f.replace("Month_", "Month: ")))
        coefs = pd.Series(logit[-1].coef_[0], index=X.columns)
        odds = (pd.DataFrame({"feature": coefs.index, "odds_ratio_per_sd": np.exp(coefs.values)})
                .assign(feature=lambda d: d["feature"].map(lambda f: READABLE.get(f, f.replace("Month_", "Month: ")))))
        results["with_page_values" if with_pv else "without_page_values"] = {
            "logit_auc": roc_auc_score(yte, logit.predict_proba(Xte)[:, 1]),
            "rf_auc": roc_auc_score(yte, rf.predict_proba(Xte)[:, 1]),
            "importance": importance,
            "odds": odds,
        }
    return results


if __name__ == "__main__":
    d = load()
    print("sessions", len(d), "conv rate", round(d["Revenue"].mean(), 4))
    print(rate_by(d, "VisitorType"))
    print(rate_by(d, "Month"))
    print(rate_by(d, "TrafficType", 100).sort_values("conversion_rate", ascending=False))
    print(rate_by(d, "Weekend"))
    print(compare_groups(d).round(3).to_string())
    print("chi2 visitor p", chi_square(d, "VisitorType"), "month p", chi_square(d, "Month"))
    m = model_results(d)
    for k, v in m.items():
        print(k, "logit", round(v["logit_auc"], 3), "rf", round(v["rf_auc"], 3))
        print(v["importance"].head(6).round(4).to_string())
