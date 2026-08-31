"""
Auto-curate popular podcast/interview videos that expose a "most replayed"
heatmap, for building the engagement-scorer dataset.

Strategy:
  1. yt-dlp search (flat) over several podcast/interview queries -> candidate ids
  2. pre-filter by duration range and view count (heatmaps need popularity)
  3. full-probe each candidate for a `heatmap`; keep those that have one
  4. stop at TARGET videos, write URLs to an output file

Usage:
  python server/eval/curate_urls.py --n 10 --out server/eval/urls.txt
"""
from __future__ import annotations

import argparse
import yt_dlp

QUERIES = [
    "Lex Fridman podcast clip",
    "Diary of a CEO podcast",
    "Huberman Lab podcast clip",
    "startup founder interview podcast",
    "podcast interview highlight",
    "TED talk",
    "Y Combinator interview",
    "author interview podcast",
    "science podcast interview",
    "business podcast clip",
]

# Keep durations manageable for a first run (download + transcribe + SER cost).
MIN_DUR = 300      # 5 min
MAX_DUR = 1500     # 25 min
MIN_VIEWS = 200_000
SEARCH_PER_QUERY = 12
MAX_PROBES = 120


def search_candidates(query: str, n: int) -> list[dict]:
    opts = {"quiet": True, "no_warnings": True,
            "extract_flat": "in_playlist", "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{n}:{query}", download=False)
    except Exception as e:
        print(f"  search error [{query}]: {type(e).__name__}: {str(e)[:80]}")
        return []
    return [e for e in (info.get("entries") or []) if e]


def has_heatmap(vid_id: str) -> tuple[bool, dict]:
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(
                f"https://www.youtube.com/watch?v={vid_id}", download=False)
    except Exception as e:
        return False, {"err": f"{type(e).__name__}: {str(e)[:60]}"}
    return bool(info.get("heatmap")), info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10)
    ap.add_argument("--out", default="server/eval/urls.txt")
    args = ap.parse_args()

    # 1-2. gather + pre-filter candidates across queries
    seen, candidates = set(), []
    for q in QUERIES:
        for e in search_candidates(q, SEARCH_PER_QUERY):
            vid = e.get("id")
            if not vid or vid in seen:
                continue
            seen.add(vid)
            dur = e.get("duration") or 0
            views = e.get("view_count") or 0
            if MIN_DUR <= dur <= MAX_DUR and views >= MIN_VIEWS:
                candidates.append((views, vid, e.get("title", "")[:60]))
    candidates.sort(reverse=True)  # most-viewed first (more likely to have heatmap)
    print(f"Pre-filtered candidates: {len(candidates)}")

    # 3-4. probe for heatmap, keep until we have n
    kept = []
    for i, (views, vid, title) in enumerate(candidates[:MAX_PROBES]):
        ok, info = has_heatmap(vid)
        if ok:
            dur = info.get("duration")
            kept.append(vid)
            print(f"  [{len(kept)}/{args.n}] KEEP {vid}  dur={dur}s  views={views:,}  '{title}'")
            if len(kept) >= args.n:
                break
        else:
            reason = info.get("err", "no heatmap")
            print(f"       skip {vid}  ({reason})")

    if not kept:
        print("No qualifying videos found.")
        return
    urls = [f"https://www.youtube.com/watch?v={v}" for v in kept]
    with open(args.out, "w") as f:
        f.write("# Auto-curated podcast/interview videos with most-replayed heatmaps\n")
        f.write("\n".join(urls) + "\n")
    print(f"\nWrote {len(urls)} URLs -> {args.out}")


if __name__ == "__main__":
    main()
