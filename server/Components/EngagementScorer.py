"""
Production engagement scorer.

Re-ranks candidate highlight clips using the model fitted by the eval harness
(server/eval/evaluate_scorer.py), which was trained to predict YouTube
"most replayed" intensity from grounded audio/text features.

Design:
  - Loads a saved model bundle {model, features, kind} if present.
  - Falls back to transparent hand-set weights when no model is available, so the
    pipeline always runs (e.g. before a model has been fitted, or in a fresh deploy).
  - Scores a feature dict; re-ranks a list of candidates.

The empirical finding behind this (see notes): the features predict within-video
replay on reaction/hype content (audible-event driven), and speech arousal is the
strongest single signal — hence the fallback weights lean on it. On content whose
replays are semantic/content-driven (e.g. lectures) the signal is weak; treat the
score as a re-ranking hint over LLM-proposed candidates, not ground truth.
"""
from __future__ import annotations

import os

# Fallback weights over normalized features when no fitted model is present.
# speech_arousal is the workhorse; energy contributes; text a little.
_FALLBACK_WEIGHTS = {
    "speech_arousal": 0.45,
    "rms_mean": 0.20,
    "rms_std": 0.10,
    "zcr_mean": 0.10,
    "text_intensity": 0.15,
}

DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "eval", "data", "scorer.joblib",
)


class EngagementScorer:
    def __init__(self, model_path: str | None = None):
        self.model = None
        self.feature_names = None
        self.kind = "fallback"
        path = model_path or DEFAULT_MODEL_PATH
        if os.path.exists(path):
            try:
                import joblib
                bundle = joblib.load(path)
                self.model = bundle["model"]
                self.feature_names = bundle["features"]
                self.kind = bundle.get("kind", "model")
            except Exception as e:
                print(f"EngagementScorer: failed to load {path} ({e}); using fallback.")

    # ── scoring ────────────────────────────────────────────────────────────
    def score(self, feats: dict) -> float:
        """Score a single candidate from its feature dict. Higher = more engaging."""
        if self.model is not None:
            import pandas as pd
            x = pd.DataFrame([[feats.get(f, 0.0) for f in self.feature_names]],
                             columns=self.feature_names)  # named cols: no sklearn warning
            return float(self.model.predict(x)[0])
        # fallback: weighted sum of the features we have
        return float(sum(w * feats.get(f, 0.0) for f, w in _FALLBACK_WEIGHTS.items()))

    def rerank(self, candidates: list[dict], feats_key: str = "features") -> list[dict]:
        """
        Sort candidates (each a dict with a `features` sub-dict) by engagement score,
        descending. Attaches `engagement_score` to each and returns a new list.
        """
        scored = []
        for c in candidates:
            s = self.score(c.get(feats_key, {}))
            scored.append({**c, "engagement_score": s})
        scored.sort(key=lambda c: c["engagement_score"], reverse=True)
        return scored


# Module-level singleton for convenience in the pipeline.
_default = None


def get_scorer() -> EngagementScorer:
    global _default
    if _default is None:
        _default = EngagementScorer()
    return _default
