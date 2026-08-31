"""
Grounded feature extractors for the engagement scorer.

Each candidate clip / window is described by measurable signals:
  - Audio energy & dynamics (librosa)     -> how loud / dynamic the delivery is
  - Speech emotion / arousal (wav2vec2)   -> HOW it was said (tone, prosody)
  - Text emotion intensity (DistilRoBERTa)-> emotional content of the words

These are the inputs the scorer combines. Models are loaded lazily and cached
so building a dataset over many windows only pays the load cost once.
"""
from __future__ import annotations

import _compat  # noqa: F401  (installs lzma stub before librosa/joblib) - must be first
import functools
import numpy as np

# NOTE: Audio is loaded with soundfile (not librosa.load) to keep things simple;
# librosa is used for feature math. The _compat import above handles the missing
# _lzma extension that librosa's pooch dependency and joblib reference on import.

# Target sample rate for the speech-emotion model (wav2vec2 expects 16 kHz mono).
SER_SR = 16000

# Feature column order the scorer/eval rely on. Keep stable.
AUDIO_FEATURES = [
    "rms_mean", "rms_std", "rms_max",
    "pitch_mean", "pitch_std",
    "tempo",
    "zcr_mean",
    "centroid_mean",
]
SPEECH_FEATURES = ["speech_arousal"]
TEXT_FEATURES = ["text_intensity"]
FEATURE_COLUMNS = AUDIO_FEATURES + SPEECH_FEATURES + TEXT_FEATURES


# ── Audio (librosa) ────────────────────────────────────────────────────────
def audio_features(y: np.ndarray, sr: int) -> dict:
    """Cheap, grounded DSP features for an audio window. No model needed."""
    import librosa

    if y.size == 0:
        return {k: 0.0 for k in AUDIO_FEATURES}

    rms = librosa.feature.rms(y=y)[0]
    zcr = librosa.feature.zero_crossing_rate(y=y)[0]
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]

    # Pitch via pyin is accurate but slow; piptrack is fast enough per-window.
    try:
        pitches, mags = librosa.piptrack(y=y, sr=sr)
        pitch_vals = pitches[mags > np.median(mags)]
        pitch_vals = pitch_vals[pitch_vals > 0]
    except Exception:
        pitch_vals = np.array([])

    try:
        tempo = float(librosa.feature.tempo(y=y, sr=sr)[0])
    except Exception:
        tempo = 0.0

    return {
        "rms_mean": float(np.mean(rms)),
        "rms_std": float(np.std(rms)),
        "rms_max": float(np.max(rms)),
        "pitch_mean": float(np.mean(pitch_vals)) if pitch_vals.size else 0.0,
        "pitch_std": float(np.std(pitch_vals)) if pitch_vals.size else 0.0,
        "tempo": tempo,
        "zcr_mean": float(np.mean(zcr)),
        "centroid_mean": float(np.mean(centroid)),
    }


# ── Speech emotion / arousal (wav2vec2) ────────────────────────────────────
@functools.lru_cache(maxsize=1)
def _ser_pipeline():
    from transformers import pipeline
    return pipeline(
        "audio-classification",
        model="superb/wav2vec2-base-superb-er",
        top_k=None,
    )

# Which emotion labels count as "high arousal" (excitement/tension proxy).
_HIGH_AROUSAL = {"hap", "ang", "happy", "angry", "surprise", "surprised", "fear"}


def speech_arousal(y_16k: np.ndarray) -> dict:
    """
    Run speech-emotion recognition on a 16 kHz mono window.
    Returns an arousal score in [0,1] = summed prob of high-arousal emotions.
    """
    if y_16k.size < SER_SR // 2:  # need at least ~0.5s
        return {"speech_arousal": 0.0}
    try:
        preds = _ser_pipeline()(
            {"array": y_16k.astype(np.float32), "sampling_rate": SER_SR}
        )
    except Exception:
        return {"speech_arousal": 0.0}
    arousal = sum(
        p["score"] for p in preds if p["label"].lower() in _HIGH_AROUSAL
    )
    return {"speech_arousal": float(min(max(arousal, 0.0), 1.0))}


# ── Text emotion intensity (DistilRoBERTa) ─────────────────────────────────
@functools.lru_cache(maxsize=1)
def _text_pipeline():
    from transformers import pipeline
    return pipeline(
        "text-classification",
        model="j-hartmann/emotion-english-distilroberta-base",
        top_k=None,
        truncation=True,
    )


def text_intensity(text: str) -> dict:
    """
    Emotional intensity of the transcript text in a window, in [0,1]:
    1 - P(neutral). High when the words carry strong emotion.
    """
    text = (text or "").strip()
    if not text:
        return {"text_intensity": 0.0}
    try:
        preds = _text_pipeline()(text[:1000])[0]
    except Exception:
        return {"text_intensity": 0.0}
    neutral = next(
        (p["score"] for p in preds if p["label"].lower() == "neutral"), 0.0
    )
    return {"text_intensity": float(min(max(1.0 - neutral, 0.0), 1.0))}


def extract_window_features(y_win: np.ndarray, sr: int,
                            y_win_16k: np.ndarray, text: str) -> dict:
    """All features for a single window, as a flat dict keyed by FEATURE_COLUMNS."""
    feats = {}
    feats.update(audio_features(y_win, sr))
    feats.update(speech_arousal(y_win_16k))
    feats.update(text_intensity(text))
    return feats
