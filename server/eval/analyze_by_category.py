"""
Per-category analysis of the engagement scorer on a mixed dataset.

Runs leave-one-video-out ridge and reports Spearman overall and PER content
category, both with and without the crowd_reaction feature. The interesting
question: does the scorer (and laughter/applause detection specifically) work
better on some content types than others?

Usage:
  python server/eval/analyze_by_category.py \
      --data server/eval/data/dataset_mixed32.csv \
      --cats server/eval/data/mixed32_categories.json
"""
from __future__ import annotations

import _compat  # noqa: F401  keep first
import argparse
import json
import numpy as np
import pandas as pd
from collections import defaultdict
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

import features as F


def lovo_per_video(df: pd.DataFrame, cols: list[str]) -> dict:
    """Leave-one-video-out ridge; return {video_id: spearman}."""
    out = {}
    for vid in df["video_id"].unique():
        tr, te = df[df.video_id != vid], df[df.video_id == vid]
        if len(te) < 3 or te["label"].std() == 0:
            continue
        m = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
        m.fit(tr[cols], tr["label"])
        sp = spearmanr(m.predict(te[cols]), te["label"]).correlation
        if not np.isnan(sp):
            out[vid] = sp
    return out


def summarize(per_video: dict, cats: dict, label: str):
    by_cat = defaultdict(list)
    for vid, sp in per_video.items():
        by_cat[cats.get(vid, "?")].append(sp)
    allv = list(per_video.values())
    print(f"\n=== {label} (mean Spearman, leave-one-video-out) ===")
    print(f"  {'OVERALL':10s} {np.mean(allv):+.3f} ± {np.std(allv):.3f}  (n={len(allv)})")
    for cat in sorted(by_cat):
        v = by_cat[cat]
        print(f"  {cat:10s} {np.mean(v):+.3f} ± {np.std(v):.3f}  (n={len(v)})")
    return {c: float(np.mean(v)) for c, v in by_cat.items()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="server/eval/data/dataset_mixed32.csv")
    ap.add_argument("--cats", default="server/eval/data/mixed32_categories.json")
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    cats = json.load(open(args.cats))
    print(f"Loaded {len(df)} windows from {df['video_id'].nunique()} videos")

    full = F.FEATURE_COLUMNS
    nocrowd = [c for c in full if c != "crowd_reaction"]

    without = summarize(lovo_per_video(df, nocrowd), cats, "WITHOUT crowd_reaction")
    with_ = summarize(lovo_per_video(df, full), cats, "WITH crowd_reaction")

    print("\n=== crowd_reaction lift per category (with - without) ===")
    for cat in sorted(set(without) | set(with_)):
        d = with_.get(cat, 0) - without.get(cat, 0)
        print(f"  {cat:10s} {d:+.3f}")


if __name__ == "__main__":
    main()
