"""
Speaker diarization: "who spoke when", via pyannote.audio (speaker-diarization-3.1).

Used to label captions by speaker and to reinforce the active-speaker reframe. Real
multimodal ML: a neural segmentation model + speaker embeddings + clustering.

pyannote 3.x is older than our stack (numpy 2, torch 2.6, new huggingface_hub), so three
small compatibility shims are applied *only* while the pipeline loads, contained here so
the rest of the app is untouched:
  - np.NaN (removed in numpy 2) -> np.nan
  - hf_hub_download(use_auth_token=...) -> drop the removed kwarg
  - torch.load weights_only=False for our own trusted cached checkpoint

Note: pyannote/speaker-diarization-3.1 is a gated HF model. It works here because the
weights are already in the local HF cache. A fresh machine needs an HF token and must
accept the model's license once.
"""
from __future__ import annotations

import os
import subprocess
import tempfile

# Bright, high-contrast caption highlight colors, assigned to speakers by order of
# appearance. Readable on any footage with the caption's black stroke.
SPEAKER_COLORS = ["#22DD7A", "#29BFFF", "#FFCB2E", "#FF5CA8", "#FF8A3D"]

_PIPELINE = None


def _get_pipeline():
    global _PIPELINE
    if _PIPELINE is not None:
        return _PIPELINE

    import numpy as np
    import torch
    import huggingface_hub as H

    if not hasattr(np, "NaN"):
        np.NaN = np.nan
    # Gated model: authenticate with an HF token from the environment. huggingface_hub
    # reads HF_TOKEN automatically, but we also pass it explicitly to pyannote and mirror
    # it to the standard env names so any internal download picks it up too.
    token = (os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_HUB_TOKEN")
             or os.getenv("HUGGING_FACE_HUB_TOKEN"))
    if token:
        os.environ.setdefault("HF_TOKEN", token)
        os.environ.setdefault("HUGGINGFACE_HUB_TOKEN", token)

    orig_dl, orig_load = H.hf_hub_download, torch.load
    H.hf_hub_download = lambda *a, **k: (k.pop("use_auth_token", None), orig_dl(*a, **k))[1]
    torch.load = lambda *a, **k: orig_load(*a, **{**k, "weights_only": False})
    try:
        from pyannote.audio import Pipeline
        _PIPELINE = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1", use_auth_token=token)
    finally:
        torch.load = orig_load          # restore; keep the benign hub shim
    return _PIPELINE


def diarize(audio_path: str, num_speakers: int | None = None) -> list[tuple]:
    """Return [(start_s, end_s, speaker_label)] sorted by start time."""
    import torchaudio
    pipe = _get_pipeline()
    waveform, sr = torchaudio.load(audio_path)
    kwargs = {"num_speakers": num_speakers} if num_speakers else {}
    diar = pipe({"waveform": waveform, "sample_rate": sr}, **kwargs)
    return sorted((float(seg.start), float(seg.end), label)
                  for seg, _, label in diar.itertracks(yield_label=True))


def speaker_at(diarization: list[tuple], t: float) -> str | None:
    """Speaker label active at time t (the segment covering t, else the nearest)."""
    best, best_gap = None, 1e9
    for s, e, label in diarization:
        if s <= t <= e:
            return label
        gap = min(abs(t - s), abs(t - e))
        if gap < best_gap:
            best, best_gap = label, gap
    return best


def label_segments(segments: list[tuple], diarization: list[tuple]) -> list[tuple]:
    """
    Attach a speaker to each caption segment.
    segments: [(start, end, text)] -> [(start, end, text, speaker)].
    Assigns the diarized speaker whose midpoint overlap with the segment is greatest.
    """
    labeled = []
    for s, e, text in segments:
        mid = (s + e) / 2
        labeled.append((s, e, text, speaker_at(diarization, mid)))
    return labeled


def build_speaker_color_fn(video_or_audio_path: str, num_speakers: int | None = None):
    """
    Diarize a clip and return a function mapping a time (seconds) to a highlight color,
    with each speaker assigned a distinct color by order of appearance. Returns None if
    diarization fails (caller then falls back to a single highlight color).
    """
    wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_or_audio_path,
             "-ar", "16000", "-ac", "1", "-vn", wav],
            check=True, capture_output=True)
        diarization = diarize(wav, num_speakers)
    except Exception as e:
        print(f"Diarization skipped ({e}); captions use a single highlight color.")
        return None
    finally:
        try:
            os.remove(wav)
        except OSError:
            pass
    if not diarization:
        return None

    order: list[str] = []
    for _, _, spk in diarization:
        if spk not in order:
            order.append(spk)
    color_map = {spk: SPEAKER_COLORS[i % len(SPEAKER_COLORS)]
                 for i, spk in enumerate(order)}
    print(f"Diarization: {len(order)} speakers -> colors {color_map}")

    def color_at(t: float):
        return color_map.get(speaker_at(diarization, t))
    return color_at


if __name__ == "__main__":
    import sys
    for s, e, spk in diarize(sys.argv[1])[:12]:
        print(f"  {s:6.1f} - {e:6.1f}  {spk}")
