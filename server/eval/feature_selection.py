"""
Combine datasets and do forward feature selection.

Rationale: on heterogeneous content a fitted model with all 11 features overfits
(a single energy feature beat it). Combining the reaction + mixed sets gives more
videos/diversity (lower LOVO variance), and greedy forward selection finds the
parsimonious subset that actually generalizes.

Method: start empty; repeatedly add the feature that most improves mean
leave-one-video-out Spearman; stop when nothing improves it. This is a standard,
defensible selection technique. (Selection uses the LOVO score, so the final number
is mildly optimistic - reported honestly as such.)

Usage:
  python server/eval/feature_selection.py \
      --data server/eval/data/dataset_reaction30_crowd.csv server/eval/data/dataset_mixed32.csv
"""
from __future__ import annotations

import _compat  # noqa: F401  keep first
import argparse
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

import features as F


def lovo_spearman(df: pd.DataFrame, cols: list[str]) -> float:
    sps = []
    for vid in df["video_id"].unique():
        tr, te = df[df.video_id != vid], df[df.video_id == vid]
        if len(te) < 3 or te["label"].std() == 0:
            continue
        m = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
        m.fit(tr[cols], tr["label"])
        sp = spearmanr(m.predict(te[cols]), te["label"]).correlation
        if not np.isnan(sp):
            sps.append(sp)
    return float(np.mean(sps)) if sps else 0.0


def forward_select(df: pd.DataFrame, pool: list[str]):
    selected, remaining = [], list(pool)
    best = -1.0
    print("Forward selection (metric = mean LOVO Spearman):")
    while remaining:
        scored = [(lovo_spearman(df, selected + [f]), f) for f in remaining]
        scored.sort(reverse=True)
        gain_score, gain_feat = scored[0]
        if gain_score <= best + 1e-4:   # no meaningful improvement
            break
        best = gain_score
        selected.append(gain_feat)
        remaining.remove(gain_feat)
        print(f"  + {gain_feat:16s} -> {best:+.3f}")
    return selected, best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", nargs="+", required=True)
    ap.add_argument("--out", default="server/eval/data/dataset_combined.csv")
    args = ap.parse_args()

    frames = [pd.read_csv(p) for p in args.data]
    df = pd.concat(frames, ignore_index=True).drop_duplicates(subset=["video_id", "t0"])
    df.to_csv(args.out, index=False)
    print(f"Combined {len(args.data)} sets -> {len(df)} windows, "
          f"{df['video_id'].nunique()} videos -> {args.out}\n")

    full = F.FEATURE_COLUMNS
    print(f"Baselines on combined set:")
    print(f"  all {len(full)} features : {lovo_spearman(df, full):+.3f}")
    print(f"  energy_only        : {lovo_spearman(df, ['rms_mean']):+.3f}")
    print(f"  arousal_only       : {lovo_spearman(df, ['speech_arousal']):+.3f}\n")

    selected, best = forward_select(df, full)
    print(f"\nSelected {len(selected)}/{len(full)} features: {selected}")
    print(f"Combined LOVO Spearman with selected features: {best:+.3f}")
    dropped = [f for f in full if f not in selected]
    print(f"Dropped (no generalizing signal): {dropped}")


if __name__ == "__main__":
    main()
