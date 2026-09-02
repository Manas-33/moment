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

# Query presets by content style. "reaction" targets content whose most-replayed
# moment is an AUDIBLE event (cheer/laugh/hype/excited commentary) that the audio
# features can detect - unlike TED talks where replays are content-driven.
STYLES = {
    "podcast": [
        "Lex Fridman podcast clip", "Diary of a CEO podcast",
        "Huberman Lab podcast clip", "startup founder interview podcast",
        "podcast interview highlight", "TED talk", "Y Combinator interview",
        "author interview podcast", "science podcast interview", "business podcast clip",
    ],
    "reaction": [
        "esports insane moment cast", "gaming clutch moment commentary",
        "game awards reveal crowd reaction", "Nintendo direct reaction",
        "crowd goes wild moment", "try not to laugh challenge",
        "funniest twitch moments", "hype gaming moment",
        "live reveal audience reaction", "speedrun world record reaction",
        "sports commentary crazy finish", "esports crowd eruption",
        "developers react speedrun", "funniest gaming moments compilation",
        "unbelievable comeback reaction", "live crowd reaction surprise",
        "twitch streamer funny rage", "boxing knockout crowd reaction",
        "stand up comedy crowd laughing", "poker biggest moments reaction",
    ],
}
QUERIES = STYLES["podcast"]  # overridden by --style at runtime

# Channel sources by category, for --source channels. We pull each channel's
# videos, sort by views, and keep the most-popular ones (per category quota) that
# have a heatmap - so we get each channel's hits, not its newest filler.
CHANNELS = {
    "standup": [
        "https://www.youtube.com/@NetflixIsAJoke/videos",
        "https://www.youtube.com/@ComedyCentralStandUp/videos",
        "https://www.youtube.com/@DryBarComedy/videos",
        "https://www.youtube.com/@justforlaughs/videos",
    ],
    "talent": [
        "https://www.youtube.com/@bgt/videos",
        "https://www.youtube.com/@americasgottalent/videos",
        "https://www.youtube.com/@thevoiceglobal/videos",
        "https://www.youtube.com/@TalentRecap/videos",
    ],
    "football": [
        "https://www.youtube.com/@LiverpoolFC/videos",
        "https://www.youtube.com/@ManCity/videos",
        "https://www.youtube.com/@realmadrid/videos",
        "https://www.youtube.com/@fcbarcelona/videos",
    ],
    "reaction": [
        "https://www.youtube.com/@Sidemen/videos",
        "https://www.youtube.com/@SidemenReacts/videos",
        "https://www.youtube.com/@MoreSidemen/videos",
    ],
}

# Keep durations manageable (download + transcribe + SER cost).
MIN_DUR = 240      # 4 min
MAX_DUR = 1500     # 25 min
MIN_VIEWS = 200_000
SEARCH_PER_QUERY = 20
MAX_PROBES = 400
CHANNEL_SAMPLE = 100   # how many recent uploads to pull per channel before sorting

# Per-category quotas (channels mode). Football is capped low: self-published club
# content skews to training/behind-scenes, weak for an audible-event scorer.
QUOTAS = {"standup": 10, "talent": 10, "football": 4, "reaction": 8}

# Title substrings to skip per category (calm, no-crowd content that hurts signal).
EXCLUDE_TITLE = {
    "football": ("inside training", "training", "first day", "first training",
                 "press conference", "unveiled", "medical", "presentation",
                 "signs for", "behind the scenes", "u18", "u21", "academy"),
}


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


def channel_candidates(channel_url: str, n: int) -> list[dict]:
    """Flat-list a channel's uploads (most recent n)."""
    opts = {"quiet": True, "no_warnings": True,
            "extract_flat": "in_playlist", "skip_download": True, "playlistend": n}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(channel_url, download=False)
    except Exception as e:
        print(f"  channel error [{channel_url}]: {type(e).__name__}: {str(e)[:80]}")
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


def _probe_keep(candidates: list[tuple], quota: int, kept: list, label: str):
    """candidates: [(views, vid, title)] sorted desc. Probe heatmap, keep up to quota."""
    got = 0
    for views, vid, title in candidates[:MAX_PROBES]:
        if got >= quota:
            break
        ok, info = has_heatmap(vid)
        if ok:
            kept.append(vid)
            got += 1
            v = f"{views:,}" if views else "?"
            print(f"  [{label} {got}/{quota}] KEEP {vid}  dur={info.get('duration')}s  views={v}  '{title}'")
    return got


def curate_from_search(style: str, n: int) -> list[str]:
    queries = STYLES[style]
    print(f"Source: search | style: {style} ({len(queries)} queries)")
    seen, candidates = set(), []
    for q in queries:
        for e in search_candidates(q, SEARCH_PER_QUERY):
            vid = e.get("id")
            if not vid or vid in seen:
                continue
            seen.add(vid)
            dur = e.get("duration") or 0
            views = e.get("view_count") or 0
            if MIN_DUR <= dur <= MAX_DUR and views >= MIN_VIEWS:
                candidates.append((views, vid, e.get("title", "")[:60]))
    candidates.sort(reverse=True)
    print(f"Pre-filtered candidates: {len(candidates)}")
    kept = []
    _probe_keep(candidates, n, kept, "all")
    return kept


def curate_from_channels(per_category: int) -> list[str]:
    print(f"Source: channels | quotas: {QUOTAS}")
    seen, kept = set(), []
    for cat, urls in CHANNELS.items():
        quota = QUOTAS.get(cat, per_category)
        excludes = EXCLUDE_TITLE.get(cat, ())
        cands = []
        for ch in urls:
            for e in channel_candidates(ch, CHANNEL_SAMPLE):
                vid = e.get("id")
                if not vid or vid in seen:
                    continue
                seen.add(vid)
                dur = e.get("duration") or 0
                title = (e.get("title") or "")
                if excludes and any(x in title.lower() for x in excludes):
                    continue
                if MIN_DUR <= dur <= MAX_DUR:
                    cands.append((e.get("view_count") or 0, vid, title[:60]))
        cands.sort(reverse=True)  # most-viewed within the category first
        print(f"[{cat}] {len(cands)} duration-ok candidates; probing for heatmaps (quota {quota})...")
        _probe_keep(cands, quota, kept, cat)
    return kept


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10, help="total videos (search mode)")
    ap.add_argument("--out", default="server/eval/urls.txt")
    ap.add_argument("--source", choices=["search", "channels"], default="search")
    ap.add_argument("--style", choices=list(STYLES), default="podcast")
    ap.add_argument("--per-category", type=int, default=8,
                    help="videos per category (channels mode)")
    args = ap.parse_args()

    if args.source == "channels":
        kept = curate_from_channels(args.per_category)
    else:
        kept = curate_from_search(args.style, args.n)

    if not kept:
        print("No qualifying videos found.")
        return
    urls = [f"https://www.youtube.com/watch?v={v}" for v in kept]
    with open(args.out, "w") as f:
        f.write("# Auto-curated videos with most-replayed heatmaps\n")
        f.write("\n".join(urls) + "\n")
    print(f"\nWrote {len(urls)} URLs -> {args.out}")


if __name__ == "__main__":
    main()
