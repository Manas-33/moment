from dotenv import load_dotenv
import os
import json

from Components.llm_client import claude_chat

load_dotenv()

if not os.getenv("ANTHROPIC_API_KEY"):
    raise ValueError(
        "ANTHROPIC_API_KEY not found. Make sure it is defined in the .env file."
    )


def extract_times(json_string):
    try:

        data = json.loads(json_string)

        start_time = float(data[0]["start"])
        end_time = float(data[0]["end"])

        start_time_int = int(start_time)
        end_time_int = int(end_time)
        return start_time_int, end_time_int
    except Exception as e:
        print(f"Error in extract_times: {e}")
        return 0, 0


def _extract_multiple_highlights(json_string):
    """Parse the LLM response into a list of (start, end) tuples, sorted by start time."""
    try:
        data = json.loads(json_string)
        if not isinstance(data, list):
            data = [data]

        highlights = []
        for item in data:
            start = int(float(item["start"]))
            end = int(float(item["end"]))
            if start < end:
                highlights.append((start, end))

        highlights.sort(key=lambda h: h[0])
        return highlights
    except Exception as e:
        print(f"Error in _extract_multiple_highlights: {e}")
        return []


def _deduplicate_highlights(highlights, min_gap_seconds=10):
    """Remove overlapping or near-duplicate highlights, keeping the first occurrence."""
    if not highlights:
        return []

    deduped = [highlights[0]]
    for start, end in highlights[1:]:
        prev_start, prev_end = deduped[-1]
        if start >= prev_end + min_gap_seconds:
            deduped.append((start, end))
    return deduped


# Short-form clip length guardrails (seconds). The prompt asks for content-driven
# lengths (~15-45s, up to ~60s); these are the hard safety net so a stray LLM answer
# can't produce a 3-second accident or a clip that just keeps going.
MIN_CLIP_SEC = 10
MAX_CLIP_SEC = 75


def _enforce_bounds(highlights):
    """Drop clips shorter than MIN_CLIP_SEC and hard-cap clips longer than MAX_CLIP_SEC."""
    bounded = []
    for start, end in highlights:
        dur = end - start
        if dur < MIN_CLIP_SEC:
            print(f"Dropping too-short highlight ({start}-{end}, {dur}s)")
            continue
        if dur > MAX_CLIP_SEC:
            print(f"Capping long highlight ({start}-{end}, {dur}s) to {MAX_CLIP_SEC}s")
            end = start + MAX_CLIP_SEC
        bounded.append((start, end))
    return bounded


SINGLE_HIGHLIGHT_SYSTEM = """You are given a timestamped transcription of a video.
Find the single most engaging moment that works as a standalone short-form video (TikTok / YouTube Short / Instagram Reel).

Rules:
- It must be ONE continuous segment (a single start and end).
- Make it only as long as it needs to be to land one complete, self-contained idea (hook -> point -> payoff), and not a second longer. Aim for 15-45 seconds; go up to about 60 only if the moment genuinely needs it. Never shorter than 10 seconds or longer than 75 seconds. Do not pad it to reach a length.
- Start on a strong hook and end on a natural conclusion — never begin or cut off mid-sentence.

Return ONLY valid JSON, nothing else:
[{"start": <seconds>, "content": "Highlight text", "end": <seconds>}]
"""

MULTI_HIGHLIGHT_SYSTEM = """You are given a timestamped transcription of a long video.
Your job is to find the {num_highlights} most engaging, viral-worthy highlights that can each be used as a standalone short-form video (TikTok / YouTube Short / Instagram Reel).

Rules:
1. Each highlight MUST be a single continuous segment (one start and one end).
2. Make each clip only as long as it needs to be to land ONE complete, self-contained idea — a hook, the point, and a payoff — and not a second longer. Length should fit the moment, NOT a fixed target: most clips work best at 15-45 seconds; go up to about 60 seconds only when the moment genuinely needs it. Never pad a clip to fill time. Never shorter than 10 seconds or longer than 75 seconds. It is good for the {num_highlights} clips to have DIFFERENT lengths.
3. Optimize for completion: pick moments a viewer will watch to the very end and re-loop — that is what the platforms reward.
4. Each clip must start on a strong hook (grab attention in the first few seconds) and end on a natural conclusion — never begin or cut off mid-sentence, and never trail into filler.
5. All {num_highlights} highlights MUST come from DIFFERENT parts of the video — no overlapping time ranges.
6. Spread the highlights across the full length of the video so the audience sees variety.
7. Rank them by virality / engagement potential (best first).
8. Each highlight should be self-contained and make sense without extra context.

Return ONLY valid JSON — no markdown, no explanation, no extra text.

Format (array of exactly {num_highlights} objects):
[
  {{"start": <seconds>, "end": <seconds>, "content": "Brief description of why this is engaging"}},
  ...
]

start and end must be numbers (seconds from the beginning of the video).
"""


def GetHighlight(Transcription):
    """Get a single highlight from a transcription. Kept for backwards compatibility."""
    print("Getting Highlight from Transcription")
    try:
        user_msg = Transcription + SINGLE_HIGHLIGHT_SYSTEM

        json_string = claude_chat(SINGLE_HIGHLIGHT_SYSTEM, user_msg, temperature=0.7)
        json_string = json_string.replace("json", "").replace("```", "")
        print("Json String: ", json_string)
        Start, End = extract_times(json_string)
        if Start == End:
            for i in range(3):
                print(f"Retrying highlight extraction (attempt {i+1}/3)")
                json_string = claude_chat(
                    SINGLE_HIGHLIGHT_SYSTEM,
                    user_msg,
                    temperature=0.7 + (i * 0.1),
                )
                json_string = json_string.replace("json", "").replace("```", "")
                Start, End = extract_times(json_string)
                if Start != End:
                    break
        return Start, End

    except Exception as e:
        print(f"Error in GetHighlight: {e}")
        return 0, 0


def GetMultipleHighlights(transcription, num_highlights=3, max_retries=2):
    """
    Get multiple distinct, non-overlapping highlights from a transcription in one LLM call.

    Returns a list of (start, end) tuples sorted by engagement (best first).
    Falls back to repeated single-highlight calls if the multi-call fails.
    """
    print(f"Getting {num_highlights} highlights from transcription")

    if num_highlights <= 0:
        return []
    if num_highlights == 1:
        start, end = GetHighlight(transcription)
        return _enforce_bounds([(start, end)]) if start != end else []

    system_prompt = MULTI_HIGHLIGHT_SYSTEM.replace("{num_highlights}", str(num_highlights))

    for attempt in range(1 + max_retries):
        try:
            temp = 0.7 + (attempt * 0.1)
            print(f"Multi-highlight attempt {attempt + 1}/{1 + max_retries} (temperature={temp})")

            raw = claude_chat(system_prompt, transcription, temperature=temp)
            raw = raw.replace("json", "").replace("```", "").strip()
            print(f"Raw LLM response: {raw[:500]}")

            highlights = _extract_multiple_highlights(raw)
            highlights = _deduplicate_highlights(highlights)
            highlights = _enforce_bounds(highlights)

            if len(highlights) >= num_highlights:
                return highlights[:num_highlights]

            if highlights:
                print(f"Got {len(highlights)}/{num_highlights} highlights, retrying for more")
            else:
                print("No valid highlights parsed, retrying")

        except Exception as e:
            print(f"Error in GetMultipleHighlights attempt {attempt + 1}: {e}")

    # Fallback: call GetHighlight individually, excluding already-found ranges
    print("Falling back to individual GetHighlight calls")
    if 'highlights' not in locals() or not highlights:
        highlights = []

    already_used = set()
    for start, end in highlights:
        already_used.update(range(start, end))

    while len(highlights) < num_highlights:
        start, end = GetHighlight(transcription)
        if start == 0 and end == 0:
            break
        overlap = any(s <= start < e or s < end <= e for s, e in highlights)
        if not overlap:
            highlights.append((start, end))
        else:
            print(f"Skipping overlapping fallback highlight ({start}-{end})")
            break

    return _enforce_bounds(highlights)[:num_highlights]


if __name__ == "__main__":
    User = "Any Example"
    print(GetHighlight(User))
