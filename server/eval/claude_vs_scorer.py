"""
The experiment that actually matters: does the scorer re-ranking Claude's candidates
pick MORE-REPLAYED clips than Claude's own ranking?

Per video:
  1. Claude OVER-generates N candidate clips from the transcript (its semantic ranking,
     best-first) - this is what makes re-ranking meaningful.
  2. Score each candidate with the engagement scorer (4-feature model on the clip audio+text).
  3. Judge each ranking's top-K clips by their ACTUAL YouTube most-replayed value:
       - claude   : Claude's own top-K
       - scorer   : scorer's re-ranked top-K
       - oracle   : best-possible top-K among Claude's candidates (ceiling)
       - random   : average of random top-K (floor)
  4. skill = (approach - random) / (oracle - random)  in [0,1], comparable across videos.

If skill(scorer) > skill(claude), re-ranking earns its place. If not, Claude-alone is the
honest baseline and the scorer is a marginal/​content-specific add-on.

Usage:
  python server/eval/claude_vs_scorer.py --data data/dataset_combined.csv --candidates 8 --k 3
"""
from __future__ import annotations

import _compat  # noqa: F401  keep first
import argparse
import gc
import json
import os
import sys

import numpy as np
import pandas as pd
from dotenv import load_dotenv

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.dirname(HERE)
sys.path.insert(0, SERVER)
sys.path.insert(0, os.path.join(SERVER, "Components"))
sys.path.insert(0, HERE)
load_dotenv(os.path.join(SERVER, ".env"))  # ANTHROPIC_API_KEY

import features as F  # noqa: E402
from build_dataset import fetch_info, heatmap_value  # noqa: E402
from Components.LanguageTasks import GetMultipleHighlights  # noqa: E402
from Components.EngagementScorer import EngagementScorer  # noqa: E402

CACHE = os.path.join(HERE, "data", "cache")


def load_cached(vid: str):
    wav = os.path.join(CACHE, f"{vid}.wav")
    tj = os.path.join(CACHE, f"{vid}.json")
    if not (os.path.exists(wav) and os.path.exists(tj)):
        return None, None
    import soundfile as sf
    y, sr = sf.read(wav, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    segs = [tuple(x) for x in json.load(open(tj))]
    return (y, sr), segs


def trans_text(segs) -> str:
    # same format the production pipeline feeds the LLM (tasks.py)
    return "".join(f"{s} - {e}: {t}" for s, e, t in segs)


def text_in(segs, a, b) -> str:
    return " ".join(t.strip() for s, e, t in segs if a <= (s + e) / 2 < b)


def topk_value(actual: list[float], order: list[int], k: int) -> float:
    return float(sum(actual[i] for i in order[:k]))


def process(vid: str, scorer, n_cand: int, k: int, rng) -> dict | None:
    audio, segs = load_cached(vid)
    if audio is None or not segs:
        return None
    info = fetch_info(f"https://www.youtube.com/watch?v={vid}")
    heatmap = (info or {}).get("heatmap")
    if not heatmap:
        return None
    y, sr = audio

    cands = GetMultipleHighlights(trans_text(segs), num_highlights=n_cand)  # Claude order
    cands = [(int(s), int(e)) for s, e in cands if e > s]
    if len(cands) < k + 1:
        return None

    scores, actual = [], []
    for (s, e) in cands:
        yseg = y[int(s * sr):int(e * sr)]
        feats = F.extract_window_features(yseg, sr, yseg, text_in(segs, s, e))
        scores.append(scorer.score(feats))
        actual.append(heatmap_value(heatmap, s, e))

    n = len(cands)
    claude_order = list(range(n))                       # Claude best-first
    scorer_order = sorted(range(n), key=lambda i: -scores[i])
    oracle_order = sorted(range(n), key=lambda i: -actual[i])

    claude_v = topk_value(actual, claude_order, k)
    scorer_v = topk_value(actual, scorer_order, k)
    oracle_v = topk_value(actual, oracle_order, k)
    rand_v = float(np.mean([
        topk_value(actual, list(rng.permutation(n)), k) for _ in range(200)]))

    denom = oracle_v - rand_v
    def skill(v):  # 0=random, 1=oracle
        return (v - rand_v) / denom if denom > 1e-9 else np.nan
    result = {"vid": vid, "n_cand": n,
              "claude": skill(claude_v), "scorer": skill(scorer_v),
              "claude_vc": claude_v / oracle_v if oracle_v > 0 else np.nan,
              "scorer_vc": scorer_v / oracle_v if oracle_v > 0 else np.nan}
    # release the big audio array before the next video so memory stays bounded
    del y, audio
    gc.collect()
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/dataset_combined.csv")
    ap.add_argument("--candidates", type=int, default=8)
    ap.add_argument("--k", type=int, default=3)
    ap.add_argument("--limit", type=int, default=0, help="cap #videos (0=all) for a quick test")
    args = ap.parse_args()

    out_path = "data/claude_vs_scorer_results.csv"
    vids = list(pd.read_csv(args.data)["video_id"].unique())
    if args.limit:
        vids = vids[:args.limit]

    # Resume: skip videos already saved so an interrupted run continues where it stopped.
    done = set()
    if os.path.exists(out_path):
        done = set(pd.read_csv(out_path)["vid"].astype(str))
    todo = [v for v in vids if str(v) not in done]

    scorer = EngagementScorer()
    print(f"Scorer: {scorer.kind} | features={scorer.feature_names}")
    print(f"Over-generate {args.candidates} candidates, pick top-{args.k}. "
          f"{len(done)} done, {len(todo)} remaining.\n")

    rng = np.random.RandomState(0)
    for i, vid in enumerate(todo, 1):
        try:
            r = process(vid, scorer, args.candidates, args.k, rng)
        except Exception as e:
            print(f"[{i}/{len(todo)}] {vid}: ERROR {type(e).__name__}: {str(e)[:80]}")
            continue
        if r:
            # append immediately so progress survives an interruption / sleep
            pd.DataFrame([r]).to_csv(
                out_path, mode="a", header=not os.path.exists(out_path), index=False)
            print(f"[{i}/{len(todo)}] {vid}: claude_skill={r['claude']:+.2f} "
                  f"scorer_skill={r['scorer']:+.2f}  (n_cand={r['n_cand']})")

    if not os.path.exists(out_path):
        print("No usable videos."); return
    df = pd.read_csv(out_path)
    print(f"\n=== RESULT over {len(df)} videos (skill: 0=random pick, 1=oracle pick) ===")
    for col in ["claude", "scorer"]:
        print(f"  {col:8s} skill = {df[col].mean():+.3f} ± {df[col].std():.3f}   "
              f"value-captured = {df[col+'_vc'].mean()*100:.1f}%")
    win = (df["scorer"] > df["claude"]).mean() * 100
    print(f"\n  scorer beats claude on {win:.0f}% of videos")
    print(f"  mean skill lift from re-ranking: {(df['scorer']-df['claude']).mean():+.3f}")


if __name__ == "__main__":
    main()
