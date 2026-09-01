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
# Crowd reaction (laughter/applause/cheering) from an AudioSet-tagged model.
# Strong "audible event" signal that plain energy/emotion features miss.
EVENT_FEATURES = ["crowd_reaction"]
FEATURE_COLUMNS = AUDIO_FEATURES + SPEECH_FEATURES + TEXT_FEATURES + EVENT_FEATURES


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


# ── Crowd reaction: laughter / applause / cheering (AudioSet AST) ───────────
@functools.lru_cache(maxsize=1)
def _audio_tag_pipeline():
    from transformers import pipeline
    return pipeline(
        "audio-classification",
        model="MIT/ast-finetuned-audioset-10-10-0.4593",
        top_k=None,
    )

# AudioSet display-name substrings that count as a crowd reaction.
_CROWD_KEYWORDS = (
    "laugh", "giggle", "chuckle", "chortle", "snicker",
    "applause", "clap", "cheer", "crowd", "whoop", "shout",
)


def crowd_reaction_score(y_slice_16k: np.ndarray) -> float:
    """
    Summed probability of laughter/applause/cheering/crowd classes for one audio
    slice (16 kHz mono), in [0,1]. AST expects ~10 s clips, so callers slice.
    """
    if y_slice_16k.size < SER_SR // 2:
        return 0.0
    try:
        preds = _audio_tag_pipeline()(
            {"array": y_slice_16k.astype(np.float32), "sampling_rate": SER_SR}
        )
    except Exception:
        return 0.0
    score = sum(
        p["score"] for p in preds
        if any(k in p["label"].lower() for k in _CROWD_KEYWORDS)
    )
    return float(min(max(score, 0.0), 1.0))


def extract_window_features(y_win: np.ndarray, sr: int,
                            y_win_16k: np.ndarray, text: str,
                            crowd_reaction: float = 0.0) -> dict:
    """
    All features for a single window, as a flat dict keyed by FEATURE_COLUMNS.

    `crowd_reaction` is passed in (computed once per video from a sliced AST pass)
    rather than recomputed here, because AST truncates to ~10 s and laughter can
    fall anywhere in the window.
    """
    feats = {}
    feats.update(audio_features(y_win, sr))
    feats.update(speech_arousal(y_win_16k))
    feats.update(text_intensity(text))
    feats["crowd_reaction"] = float(crowd_reaction)
    return feats
