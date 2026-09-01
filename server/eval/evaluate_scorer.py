"""
Evaluate the engagement scorer against the YouTube "most replayed" ground truth.

Method:
  - Leave-One-Video-Out cross-validation (best use of a small video set): train on
    all-but-one video's windows, predict on the held-out video, rotate.
  - Per held-out video, measure how well predicted scores rank the windows against
    the actual replay-intensity label.
  - Compare the fitted model to simple baselines it must beat.

Metrics (per video, then averaged over videos):
  - Spearman / Kendall rank correlation (predicted vs actual replay over the timeline)
  - top-3 recall: fraction of the actual top-3 windows recovered in the predicted top-3
  - nDCG@3: ranking quality of the clips we'd actually export

Baselines:
  - random           : shuffle
  - energy_only      : rms_mean (a single dumb feature)
  - arousal_only     : speech_arousal
  - text_only        : text_intensity
The fitted model uses ALL features.

After CV, a final model is fit on all data and saved for production use.

Usage:
  python server/eval/evaluate_scorer.py --data server/eval/data/dataset_ted10.csv
"""
from __future__ import annotations

import _compat  # noqa: F401  installs lzma stub before sklearn/joblib - keep first
import argparse
import os
import numpy as np
import pandas as pd
from scipy.stats import spearmanr, kendalltau
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import make_pipeline

import features as F

TOPK = 3
RNG = np.random.RandomState(0)  # deterministic (scripts can't use random seeds at runtime)


def make_model(kind: str):
    if kind == "ridge":
        return make_pipeline(StandardScaler(), Ridge(alpha=1.0))
    if kind == "rf":
        return RandomForestRegressor(
            n_estimators=200, max_depth=5, min_samples_leaf=3, random_state=0)
    raise ValueError(kind)


# ── ranking metrics ────────────────────────────────────────────────────────
def ndcg_at_k(pred: np.ndarray, actual: np.ndarray, k: int) -> float:
    order = np.argsort(pred)[::-1][:k]              # rank windows by predicted score
    gains = actual[order]
    discounts = 1.0 / np.log2(np.arange(2, len(gains) + 2))
    dcg = float(np.sum(gains * discounts))
    ideal = np.sort(actual)[::-1][:k]
    idcg = float(np.sum(ideal * discounts))
    return dcg / idcg if idcg > 0 else 0.0


def topk_recall(pred: np.ndarray, actual: np.ndarray, k: int) -> float:
    kk = min(k, len(pred))
    pred_top = set(np.argsort(pred)[::-1][:kk].tolist())
    actual_top = set(np.argsort(actual)[::-1][:kk].tolist())
    return len(pred_top & actual_top) / kk


def score_metrics(pred: np.ndarray, actual: np.ndarray) -> dict:
    if len(pred) < 3 or np.std(actual) == 0:
        return {}
    sp = spearmanr(pred, actual).correlation
    kt = kendalltau(pred, actual).correlation
    return {
        "spearman": 0.0 if np.isnan(sp) else float(sp),
        "kendall": 0.0 if np.isnan(kt) else float(kt),
        "top3_recall": topk_recall(pred, actual, TOPK),
        "ndcg@3": ndcg_at_k(pred, actual, TOPK),
    }


# ── baselines ──────────────────────────────────────────────────────────────
def baseline_pred(name: str, X_test: pd.DataFrame) -> np.ndarray:
    if name == "random":
        return RNG.rand(len(X_test))
    if name == "energy_only":
        return X_test["rms_mean"].to_numpy()
    if name == "arousal_only":
        return X_test["speech_arousal"].to_numpy()
    if name == "text_only":
        return X_test["text_intensity"].to_numpy()
    raise ValueError(name)


BASELINES = ["random", "energy_only", "arousal_only", "text_only"]


def leave_one_video_out(df: pd.DataFrame, model_kind: str) -> pd.DataFrame:
    videos = df["video_id"].unique()
    rows = []
    for vid in videos:
        train = df[df["video_id"] != vid]
        test = df[df["video_id"] == vid]
        actual = test["label"].to_numpy()
        if len(test) < 3 or np.std(actual) == 0:
            continue

        # fitted model (all features)
        model = make_model(model_kind)
        model.fit(train[F.FEATURE_COLUMNS], train["label"])
        pred = model.predict(test[F.FEATURE_COLUMNS])
        m = score_metrics(pred, actual)
        if m:
            rows.append({"video_id": vid, "method": f"model_{model_kind}", "n": len(test), **m})

        # baselines
        for b in BASELINES:
            mb = score_metrics(baseline_pred(b, test), actual)
            if mb:
                rows.append({"video_id": vid, "method": b, "n": len(test), **mb})
    return pd.DataFrame(rows)


def summarize(results: pd.DataFrame) -> pd.DataFrame:
    metric_cols = ["spearman", "kendall", "top3_recall", "ndcg@3"]
    agg = results.groupby("method")[metric_cols].agg(["mean", "std"])
    # flatten for printing
    out = pd.DataFrame({m: agg[(m, "mean")].round(3).astype(str)
                        + " ± " + agg[(m, "std")].fillna(0).round(3).astype(str)
                        for m in metric_cols})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="server/eval/data/dataset_ted10.csv")
    ap.add_argument("--model", default="rf", choices=["ridge", "rf"])
    ap.add_argument("--save", default="server/eval/data/scorer.joblib")
    ap.add_argument("--min-t0", type=float, default=0.0,
                    help="drop windows starting before this time (s) to remove the "
                         "YouTube intro re-scrub spike, a structural label confound")
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    if args.min_t0 > 0:
        before = len(df)
        df = df[df["t0"] >= args.min_t0].reset_index(drop=True)
        print(f"Dropped {before - len(df)} intro windows (t0 < {args.min_t0}s)")
    n_videos = df["video_id"].nunique()
    print(f"Loaded {len(df)} windows from {n_videos} videos: {args.data}\n")
    if n_videos < 3:
        print("Need >=3 videos for leave-one-video-out CV.")
        return

    results = leave_one_video_out(df, args.model)
    print("=== Per-method metrics (mean ± std over held-out videos, higher = better) ===")
    summary = summarize(results)
    # order: fitted model first, then baselines
    order = [f"model_{args.model}"] + BASELINES
    summary = summary.reindex([m for m in order if m in summary.index])
    print(summary.to_string())

    model_row = summary.loc[f"model_{args.model}"]
    print("\n=== Headline ===")
    print(f"Fitted model ({args.model}) vs baselines on {n_videos} videos, "
          f"leave-one-video-out CV.")
    print(f"  model spearman   : {model_row['spearman']}")
    print(f"  model top3_recall: {model_row['top3_recall']}")
    print(f"  (random top3_recall baseline ~ {TOPK}/avg_windows)")

    # fit final model on all data and save for production
    final = make_model(args.model)
    final.fit(df[F.FEATURE_COLUMNS], df["label"])
    os.makedirs(os.path.dirname(args.save) or ".", exist_ok=True)
    import joblib
    joblib.dump({"model": final, "features": F.FEATURE_COLUMNS, "kind": args.model}, args.save)
    print(f"\nSaved final model -> {args.save}")

    if args.model == "ridge":
        ridge = final.named_steps["ridge"]
        coefs = sorted(zip(F.FEATURE_COLUMNS, ridge.coef_), key=lambda x: -abs(x[1]))
        print("Top feature weights:", [(f, round(c, 3)) for f, c in coefs[:5]])


if __name__ == "__main__":
    main()
