"""
Build a labeled dataset for the engagement scorer.

Ground truth = YouTube "most replayed" heatmap (per-second replay intensity,
crowd-voted engagement of the exact source content). Because we compare moments
WITHIN a single video, confounders like follower count / thumbnail / timing
cancel out.

For each input video that HAS heatmap data:
  1. download 16 kHz mono audio (yt-dlp + ffmpeg)
  2. transcribe locally with faster-whisper (text + timestamps)
  3. slide a fixed window over the timeline
  4. per window: extract grounded features (see features.py)
                 + label = mean heatmap replay value over the window
  5. append rows to a CSV

Usage:
  python server/eval/build_dataset.py --urls URL [URL ...] --out server/eval/data/dataset.csv
  python server/eval/build_dataset.py --urls-file server/eval/urls.txt
"""
from __future__ import annotations

import argparse
import os
import sys
import tempfile

import numpy as np
import pandas as pd

# Make `import features` work regardless of cwd.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import features as F  # noqa: E402

WINDOW_SEC = 30.0   # candidate clip length
STRIDE_SEC = 15.0   # overlap between windows
MIN_WINDOWS = 4     # skip videos too short to yield a few windows


# ── YouTube: heatmap + audio ───────────────────────────────────────────────
def fetch_info(url: str) -> dict | None:
    import yt_dlp
    opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"  ! info error: {type(e).__name__}: {str(e)[:100]}")
        return None


def download_audio_16k(url: str, out_dir: str) -> str | None:
    """Download bestaudio and transcode to 16 kHz mono wav."""
    import yt_dlp
    out_tmpl = os.path.join(out_dir, "%(id)s.%(ext)s")
    opts = {
        "quiet": True, "no_warnings": True,
        "format": "bestaudio/best",
        "outtmpl": out_tmpl,
        # YouTube now requires a JS runtime to solve signature challenges;
        # Node is present in this project (Next.js). Without it, downloads 403.
        "js_runtimes": {"node": {}},
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
        }],
        "postprocessor_args": ["-ar", "16000", "-ac", "1"],
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
        path = os.path.join(out_dir, f"{info['id']}.wav")
        return path if os.path.exists(path) else None
    except Exception as e:
        print(f"  ! audio error: {type(e).__name__}: {str(e)[:100]}")
        return None


def heatmap_value(heatmap: list, t0: float, t1: float) -> float:
    """Overlap-weighted mean replay value of the heatmap over [t0, t1]."""
    total_w, acc = 0.0, 0.0
    for seg in heatmap:
        s, e, v = seg["start_time"], seg["end_time"], seg["value"]
        ov = max(0.0, min(t1, e) - max(t0, s))
        if ov > 0:
            acc += v * ov
            total_w += ov
    return acc / total_w if total_w else 0.0


# ── Transcription ──────────────────────────────────────────────────────────
def transcribe(wav_path: str):
    from faster_whisper import WhisperModel
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, _ = model.transcribe(wav_path)
    return [(s.start, s.end, s.text) for s in segments]


def text_in_window(segs, t0: float, t1: float) -> str:
    """Concatenate transcript segments whose midpoint falls inside the window."""
    parts = [txt for (s, e, txt) in segs if t0 <= (s + e) / 2 < t1]
    return " ".join(p.strip() for p in parts)


# ── Per-video processing ───────────────────────────────────────────────────
def process_video(url: str, tmp_dir: str) -> list[dict]:
    print(f"- {url}")
    info = fetch_info(url)
    if not info:
        return []
    heatmap = info.get("heatmap")
    dur = info.get("duration") or 0
    if not heatmap:
        print("  skip: no heatmap")
        return []
    if dur < WINDOW_SEC * MIN_WINDOWS:
        print(f"  skip: too short ({dur}s)")
        return []

    wav = download_audio_16k(url, tmp_dir)
    if not wav:
        return []

    import soundfile as sf
    y, sr = sf.read(wav, dtype="float32")  # wav is already 16k mono (ffmpeg)
    if y.ndim > 1:
        y = y.mean(axis=1)
    segs = transcribe(wav)
    print(f"  dur={dur}s  transcript_segs={len(segs)}  extracting windows...")

    rows = []
    vid = info.get("id", "unknown")
    t0 = 0.0
    while t0 + WINDOW_SEC <= dur:
        t1 = t0 + WINDOW_SEC
        a, b = int(t0 * sr), int(t1 * sr)
        y_win = y[a:b]
        text = text_in_window(segs, t0, t1)
        feats = F.extract_window_features(y_win, sr, y_win, text)
        feats["label"] = heatmap_value(heatmap, t0, t1)
        feats["video_id"] = vid
        feats["t0"] = t0
        feats["t1"] = t1
        rows.append(feats)
        t0 += STRIDE_SEC

    print(f"  -> {len(rows)} windows")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--urls", nargs="*", default=[])
    ap.add_argument("--urls-file")
    ap.add_argument("--out", default="server/eval/data/dataset.csv")
    args = ap.parse_args()

    urls = list(args.urls)
    if args.urls_file:
        with open(args.urls_file) as f:
            urls += [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    if not urls:
        ap.error("provide --urls or --urls-file")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    all_rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for url in urls:
            all_rows.extend(process_video(url, tmp))

    if not all_rows:
        print("\nNo rows produced (no videos with heatmap data?).")
        return
    df = pd.DataFrame(all_rows)
    df.to_csv(args.out, index=False)
    print(f"\nWrote {len(df)} rows from {df['video_id'].nunique()} videos -> {args.out}")
    print(df[F.FEATURE_COLUMNS + ["label"]].describe().round(3).to_string())


if __name__ == "__main__":
    main()
