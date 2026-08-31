"""Audio transcription using local faster-whisper.

The OpenAI Whisper API path is no longer used; both entry points run the local
model so the rest of the pipeline works offline. The return shape is preserved
for callers in `GenerateCaptions.py` and elsewhere: a list with a single dict
containing ``start``, ``end``, and ``words`` (each word has ``start``, ``end``,
and ``word``).
"""

from faster_whisper import WhisperModel

_model = None


def _get_model(size: str = "base") -> WhisperModel:
    global _model
    if _model is None:
        _model = WhisperModel(size, device="cpu", compute_type="int8")
    return _model


def _segments_to_payload(segments):
    segments = list(segments)
    if not segments:
        return []

    words = []
    for seg in segments:
        for w in (seg.words or []):
            words.append({
                "start": w.start,
                "end": w.end,
                "word": " " + w.word.strip(),
            })

    return [{
        "start": segments[0].start,
        "end": segments[-1].end,
        "words": words,
    }]


def transcribe_with_api(audio_file, prompt: str | None = None):
    """Transcribe an audio file using the local faster-whisper model.

    The name is kept for backwards compatibility with callers that historically
    used the OpenAI Whisper API.
    """
    model = _get_model()
    segments, _info = model.transcribe(
        audio_file,
        word_timestamps=True,
        initial_prompt=prompt,
    )
    return _segments_to_payload(segments)


def transcribe_locally(audio_file: str, prompt: str | None = None):
    """Alias for :func:`transcribe_with_api` — kept for backwards compatibility."""
    return transcribe_with_api(audio_file, prompt)
