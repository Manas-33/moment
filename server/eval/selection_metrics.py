"""
Product-aligned evaluation: "pick the best K clips - are they good?"

Spearman rank-correlation is a poor fit for clip selection: it scores the ordering
of ALL windows (including clips we'd never pick) and cares about intra-order that is
irrelevant once K separate clips are chosen. These metrics instead judge the SHORTLIST:

  - value_captured@K : the K clips the scorer picks capture what fraction of the
                       engagement the ORACLE's best K clips would. Ignores order within K.
  - skill@K          : value normalized between random (0) and oracle (1), so it's
                       comparable across videos of different baseline replay levels.
  - precision@K      : fraction of the scorer's K picks that are in the true top-K.

Realism: windows overlap (30s / 15s stride), so selection uses NON-MAX SUPPRESSION -
pick the top-scored window, drop everything within MIN_GAP seconds, repeat - to yield
K DISTINCT clips (what the product would actually publish).

Uses leave-one-video-out with the selected 4-feature model.

Usage:
  python server/eval/selection_metrics.py --data data/dataset_combined.csv
"""
from __future__ import annotations

import _compat  # noqa: F401  keep first
import argparse
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

SELECTED = ["rms_mean", "zcr_mean", "text_intensity", "speech_arousal"]
MIN_GAP_SEC = 45.0   # picked clips must start >= this far apart (distinct moments)


def nms_pick(t0: np.ndarray, scores: np.ndarray, k: int) -> list[int]:
    """Greedy non-max suppression: top score, drop overlaps within MIN_GAP, repeat."""
    order = np.argsort(scores)[::-1]
    picked, used_t = [], []
    for i in order:
        if all(abs(t0[i] - t) >= MIN_GAP_SEC for t in used_t):
            picked.append(i)
            used_t.append(t0[i])
            if len(picked) >= k:
                break
    return picked


def value_of(labels: np.ndarray, idx: list[int]) -> float:
    return float(np.sum(labels[idx]))


def evaluate(df: pd.DataFrame, k: int, n_random: int = 50) -> dict:
    rng = np.random.RandomState(0)
    vc, skill, prec = [], [], []
    for vid in df["video_id"].unique():
        tr, te = df[df.video_id != vid], df[df.video_id == vid]
        if len(te) < k + 2 or te["label"].std() == 0:
            continue
        t0 = te["t0"].to_numpy()
        labels = te["label"].to_numpy()

        model = make_pipeline(StandardScaler(), Ridge(alpha=1.0))
        model.fit(tr[SELECTED], tr["label"])
        pred = model.predict(te[SELECTED])

        model_val = value_of(labels, nms_pick(t0, pred, k))
        oracle_val = value_of(labels, nms_pick(t0, labels, k))
        rand_vals = [value_of(labels, nms_pick(t0, rng.rand(len(labels)), k))
                     for _ in range(n_random)]
        rand_val = float(np.mean(rand_vals))

        if oracle_val <= 0:
            continue
        vc.append(model_val / oracle_val)
        denom = oracle_val - rand_val
        skill.append((model_val - rand_val) / denom if denom > 1e-9 else 0.0)

        # precision@k: picked distinct clips that land among true top-k distinct clips
        true_top = set(nms_pick(t0, labels, k))
        pred_top = set(nms_pick(t0, pred, k))
        prec.append(len(true_top & pred_top) / k)

    return {
        "value_captured": (np.mean(vc), np.std(vc)),
        "skill": (np.mean(skill), np.std(skill)),
        "precision": (np.mean(prec), np.std(prec)),
        "n": len(vc),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/dataset_combined.csv")
    ap.add_argument("--ks", type=int, nargs="+", default=[3, 5])
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    print(f"Loaded {len(df)} windows / {df['video_id'].nunique()} videos: {args.data}")
    print(f"Selection: top-K by 4-feature model, NMS gap {MIN_GAP_SEC:.0f}s (distinct clips)\n")
    print(f"{'K':>3}  {'value_captured@K':>18}  {'skill@K (rand=0,oracle=1)':>26}  {'precision@K':>14}  n")
    for k in args.ks:
        r = evaluate(df, k)
        vc, sk, pr = r["value_captured"], r["skill"], r["precision"]
        print(f"{k:>3}  {vc[0]*100:6.1f}% ± {vc[1]*100:4.1f}      "
              f"{sk[0]:+.3f} ± {sk[1]:.3f}            "
              f"{pr[0]*100:5.1f}% ± {pr[1]*100:4.1f}   {r['n']}")


if __name__ == "__main__":
    main()
