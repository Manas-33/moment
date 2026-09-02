"""
Active-speaker-following vertical reframe (modern replacement for the old
Caffe/Haar Speaker.py + crop_to_vertical).

Pipeline (mirrors how production clip tools reframe):
  1. Silero VAD (neural) -> when is anyone speaking, per frame
  2. YuNet (OpenCV's CNN face detector) -> faces + landmarks per frame
  3. Mouth-region motion (temporal frame-diff in each face's mouth ROI) -> lip movement
  4. Active-speaker attribution -> during speech, the face whose mouth is moving most is
     the speaker; otherwise the largest face; otherwise hold / center
  5. EMA trajectory smoothing + deadzone -> the crop travels smoothly, no jitter
  6. Dynamic 9:16 crop clamped to frame bounds

Writes a video-only vertical file (audio is muxed back by combine_videos), so it is a
drop-in replacement for crop_to_vertical in tasks.py.

Degrades gracefully: no faces -> center crop; no/failed audio -> largest-face tracking.
Dependency-light: OpenCV (YuNet is built in) + Silero VAD. No MediaPipe.
"""
from __future__ import annotations

import os
import subprocess
import tempfile
from collections import deque

import cv2
import numpy as np

YUNET_MODEL = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "models", "face_detection_yunet.onnx")
MOTION_WINDOW = 8          # frames of mouth-motion history (~0.25s at 30fps)
ROI_SIZE = 32              # mouth ROI is resized to this for motion diffing
EMA_ALPHA = 0.15           # crop-center smoothing (lower = smoother/slower)
DEADZONE_FRAC = 0.02       # ignore target moves smaller than this fraction of width


# ── audio / VAD ─────────────────────────────────────────────────────────────
def _extract_audio_16k(video_path: str) -> str | None:
    tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video_path, "-ar", "16000", "-ac", "1", "-vn", tmp],
            check=True, capture_output=True)
        return tmp
    except Exception:
        return None


def _speech_mask(video_path: str, fps: float, total_frames: int) -> np.ndarray:
    """Boolean [total_frames]: is there speech at this frame (Silero VAD)."""
    mask = np.zeros(max(total_frames, 1), dtype=bool)
    wav = _extract_audio_16k(video_path)
    if not wav:
        return mask
    try:
        from silero_vad import load_silero_vad, get_speech_timestamps, read_audio
        model = load_silero_vad()
        audio = read_audio(wav, sampling_rate=16000)
        for seg in get_speech_timestamps(audio, model, sampling_rate=16000,
                                         return_seconds=True):
            f0, f1 = int(seg["start"] * fps), int(seg["end"] * fps)
            mask[max(0, f0):min(total_frames, f1)] = True
    except Exception as e:
        print(f"ReframeCrop: VAD unavailable ({e}); tracking largest face.")
    finally:
        try:
            os.remove(wav)
        except OSError:
            pass
    return mask


# ── mouth ROI motion ────────────────────────────────────────────────────────
def _mouth_roi(gray: np.ndarray, face_row: np.ndarray):
    """Normalized grayscale patch of the mouth region (lower-middle of the face box)."""
    x, y, w, h = face_row[:4]
    mx0, mx1 = int(x + 0.2 * w), int(x + 0.8 * w)
    my0, my1 = int(y + 0.55 * h), int(y + h)
    roi = gray[max(0, my0):max(0, my1), max(0, mx0):max(0, mx1)]
    if roi.size == 0:
        return None
    return cv2.resize(roi, (ROI_SIZE, ROI_SIZE)).astype(np.float32)


def _detector(w: int, h: int):
    det = cv2.FaceDetectorYN.create(YUNET_MODEL, "", (w, h),
                                    score_threshold=0.6, nms_threshold=0.3, top_k=50)
    det.setInputSize((w, h))
    return det


# ── main ────────────────────────────────────────────────────────────────────
def reframe_to_vertical(input_video_path: str, output_video_path: str) -> bool:
    cap = cv2.VideoCapture(input_video_path, cv2.CAP_FFMPEG)
    if not cap.isOpened():
        print("ReframeCrop: could not open video.")
        return False
    W = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    H = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    vw = min(int(H * 9 / 16), W)
    speech = _speech_mask(input_video_path, fps, total)
    detector = _detector(W, H)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (vw, H))

    smooth = target = W / 2.0
    deadzone = DEADZONE_FRAC * W
    tracks: list[dict] = []      # {cx, area, roi, hist, motion}
    idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, dets = detector.detect(frame)
        faces = dets if dets is not None else []

        seen = []
        for f in faces:
            x, y, w, h = f[:4]
            cx, area = float(x + w / 2), float(w * h)
            roi = _mouth_roi(gray, f)
            # match to an existing track by nearest center
            t = min((t for t in tracks if abs(cx - t["cx"]) < 0.08 * W),
                    key=lambda t: abs(cx - t["cx"]), default=None)
            if t is None:
                t = {"hist": deque(maxlen=MOTION_WINDOW), "roi": None}
                tracks.append(t)
            if roi is not None and t["roi"] is not None and t["roi"].shape == roi.shape:
                t["hist"].append(float(np.mean(np.abs(roi - t["roi"]))))
            t.update(cx=cx, area=area, roi=roi)
            t["motion"] = float(np.mean(t["hist"])) if t["hist"] else 0.0
            seen.append(t)
        tracks = seen or tracks[-1:]

        if len(seen) > 0:
            speaking = idx < len(speech) and speech[idx]
            if speaking and max((t["motion"] for t in seen), default=0) > 1.0:
                target = max(seen, key=lambda t: t["motion"])["cx"]
            else:
                target = max(seen, key=lambda t: t["area"])["cx"]   # largest face
        # else: hold previous target

        if abs(target - smooth) > deadzone:
            smooth += EMA_ALPHA * (target - smooth)
        x0 = int(np.clip(smooth - vw / 2, 0, max(W - vw, 0)))
        out.write(frame[:, x0:x0 + vw])
        idx += 1

    cap.release()
    out.release()
    print(f"ReframeCrop: wrote {output_video_path} ({idx} frames, {vw}x{H}).")
    return True


if __name__ == "__main__":
    import sys
    reframe_to_vertical(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "reframed.mp4")
