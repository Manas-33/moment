"""
Retrain the scorer ON THE ACTUAL TASK and test if it now beats Claude.

The earlier scorer failed to beat Claude because of a train/deploy mismatch: it was
trained on fixed 30s sliding windows vs the heatmap, then asked to rank Claude's
variable candidate clips. Here we train directly on Claude's candidates -> their real
replay value (the deployment distribution), via leave-one-video-out, and measure
value-captured@K against Claude's own ranking.

Data: data/candidates.csv (from claude_vs_scorer.py --dump-candidates), one row per
Claude candidate with its features, position/duration, and real most-replayed label.

Usage:
  python server/eval/retrain_scorer.py --data data/candidates.csv --k 3
"""
from __future__ import annotations

import _compat  # noqa: F401  keep first
import argparse
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

AUDIO = ["rms_mean", "rms_std", "rms_max", "pitch_mean", "pitch_std",
         "tempo", "zcr_mean", "centroid_mean", "speech_arousal", "text_intensity"]
CONTEXT = ["position", "dur"]

FEATURE_SETS = {
    "audio_only": AUDIO,
    "audio+context": AUDIO + CONTEXT,
    "context_only": CONTEXT,
}


def make_model(kind):
    if kind == "ridge":
        return make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    return GradientBoostingRegressor(n_estimators=150, max_depth=3,
                                     min_samples_leaf=5, random_state=0)


def value_captured(df, cols, kind, k, n_random=200):
    """Leave-one-video-out. Returns per-video value-captured for model vs Claude."""
    rng = np.random.RandomState(0)
    model_vc, claude_vc, skill_model, skill_claude = [], [], [], []
    for vid in df["vid"].unique():
        tr, te = df[df.vid != vid], df[df.vid == vid]
        if len(te) < k + 1 or te["label"].std() == 0:
            continue
        m = make_model(kind)
        m.fit(tr[cols], tr["label"])
        pred = m.predict(te[cols])
        label = te["label"].to_numpy()
        crank = te["claude_rank"].to_numpy()

        def topk_val(order):
            return float(label[order[:k]].sum())

        oracle = topk_val(np.argsort(label)[::-1])
        rand = float(np.mean([topk_val(rng.permutation(len(label))) for _ in range(n_random)]))
        mv = topk_val(np.argsort(pred)[::-1])
        cv = topk_val(np.argsort(crank))          # claude_rank ascending = best-first
        if oracle <= 0:
            continue
        model_vc.append(mv / oracle)
        claude_vc.append(cv / oracle)
        denom = oracle - rand
        skill_model.append((mv - rand) / denom if denom > 1e-9 else np.nan)
        skill_claude.append((cv - rand) / denom if denom > 1e-9 else np.nan)
    return (np.array(model_vc), np.array(claude_vc),
            np.array(skill_model), np.array(skill_claude))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/candidates.csv")
    ap.add_argument("--k", type=int, default=3)
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    print(f"Loaded {len(df)} candidates from {df['vid'].nunique()} videos "
          f"(~{len(df)/df['vid'].nunique():.1f} candidates/video)\n")

    # Claude baseline is the same regardless of feature set; compute once for reference.
    for kind in ["ridge", "gbm"]:
        print(f"### model = {kind} ###")
        for name, cols in FEATURE_SETS.items():
            mvc, cvc, sm, sc = value_captured(df, cols, kind, args.k)
            if len(mvc) == 0:
                print(f"  {name:14s}: no usable videos"); continue
            win = (mvc > cvc).mean() * 100
            print(f"  {name:14s}: retrained value-captured {mvc.mean()*100:5.1f}%  "
                  f"vs Claude {cvc.mean()*100:5.1f}%   "
                  f"skill {sm.mean():+.3f} vs {sc.mean():+.3f}   "
                  f"beats Claude {win:.0f}%")
        print()

    print("Verdict: retraining helps only if retrained value-captured / skill clearly "
          "exceeds Claude's, on the SAME videos. A wash means the signal is not in these "
          "features (likely semantic) and Claude-alone stays the baseline.")


if __name__ == "__main__":
    main()
