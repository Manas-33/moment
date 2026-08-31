import os
import tempfile
from pydub import AudioSegment
import numpy as np
from typing import List, Tuple, Optional

from deepgram import DeepgramClient

# Map the legacy OpenAI voice names this codebase used to Deepgram Aura voices,
# so existing callers that still pass things like "alloy" keep working.
_OPENAI_TO_DEEPGRAM_VOICE = {
    "alloy": "aura-asteria-en",
    "echo": "aura-orion-en",
    "fable": "aura-arcas-en",
    "onyx": "aura-zeus-en",
    "nova": "aura-luna-en",
    "shimmer": "aura-stella-en",
}

_DEFAULT_VOICE = "aura-asteria-en"


def _resolve_voice(voice: str) -> str:
    if not voice:
        return _DEFAULT_VOICE
    return _OPENAI_TO_DEEPGRAM_VOICE.get(voice, voice)


def text_to_speech(text: str, output_path: str, voice: str = "aura-asteria-en", model: str = "aura") -> bool:
    """
    Convert text to speech using Deepgram Aura.

    Args:
        text: The text to convert to speech
        output_path: Path to save the audio file (mp3)
        voice: Deepgram voice id, e.g. ``aura-asteria-en``. Legacy OpenAI voice
            names like ``alloy`` are mapped to a sensible Aura equivalent.
        model: Unused; kept for backwards compatibility with the previous OpenAI
            signature.

    Returns:
        True if successful, False otherwise
    """
    try:
        api_key = os.getenv("DEEPGRAM_API_KEY")
        if not api_key:
            print("Error in text-to-speech: DEEPGRAM_API_KEY is not set")
            return False

        client = DeepgramClient(api_key=api_key)

        audio_stream = client.speak.v1.audio.generate(
            text=text,
            model=_resolve_voice(voice),
            encoding="mp3",
        )

        with open(output_path, "wb") as f:
            for chunk in audio_stream:
                if chunk:
                    f.write(chunk)

        return True

    except Exception as e:
        print(f"Error in text-to-speech: {e}")
        return False

def transcript_to_speech(transcript: List[Tuple[str, float, float]], 
                        output_path: str, 
                        voice: str = "alloy",
                        model: str = "tts-1") -> Optional[str]:
    """
    Convert a transcript (list of text with timestamps) to speech,
    preserving the original timing to match the video
    
    Args:
        transcript: List of tuples (text, start_time, end_time)
        output_path: Path to save the final audio file
        voice: Voice to use for TTS (default: 'alloy')
        model: TTS model to use (default: 'tts-1')
        
    Returns:
        Path to the final audio file if successful, None otherwise
    """
    try:
        # Create a temporary directory for individual audio segments
        with tempfile.TemporaryDirectory() as temp_dir:
            # Process each segment
            segment_files = []
            
            # Create a silent audio segment for padding
            silence = AudioSegment.silent(duration=1000)  # 1 second of silence
            
            # Starting position (in milliseconds)
            current_position = 0
            
            # First, create all the individual audio segments
            for i, (text, start, end) in enumerate(transcript):
                segment_path = os.path.join(temp_dir, f"segment_{i}.mp3")
                
                # Skip empty text
                if not text.strip():
                    continue
                
                # Generate speech for this segment
                success = text_to_speech(text, segment_path, voice, model)
                
                if success:
                    segment_files.append((segment_path, start, end))
                else:
                    print(f"Failed to generate speech for segment: {text}")
            
            # Now create the final audio file with proper timing
            final_audio = AudioSegment.silent(duration=0)  # Start with empty audio
            
            # Calculate the maximum end time to determine the total duration
            max_end_time = max([end for _, _, end in segment_files]) if segment_files else 0
            total_duration_ms = int(max_end_time * 1000) + 1000  # Add 1 second buffer
            
            # Create a base silent audio of the total duration
            base_audio = AudioSegment.silent(duration=total_duration_ms)
            
            # Overlay each segment at the correct position
            for segment_path, start, end in segment_files:
                segment_audio = AudioSegment.from_file(segment_path)
                position_ms = int(start * 1000)
                base_audio = base_audio.overlay(segment_audio, position=position_ms)
            
            # Export the final audio
            base_audio.export(output_path, format="mp3")
            
            return output_path
            
    except Exception as e:
        print(f"Error in transcript-to-speech: {e}")
        return None

def merge_audio_with_video(video_path: str, audio_path: str, output_path: str) -> bool:
    """
    Merge audio with video using ffmpeg
    
    Args:
        video_path: Path to the video file
        audio_path: Path to the audio file
        output_path: Path to save the output video file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        import ffmpeg
        
        # Input video and audio streams
        video_stream = ffmpeg.input(video_path)
        audio_stream = ffmpeg.input(audio_path)
        
        # Merge audio and video
        output = ffmpeg.output(
            video_stream.video, 
            audio_stream.audio, 
            output_path,
            vcodec='copy',  # Copy video codec to preserve quality
            acodec='aac',   # Convert audio to AAC
            strict='experimental'
        )
        
        # Run the ffmpeg command
        ffmpeg.run(output, overwrite_output=True)
        
        return True
        
    except Exception as e:
        print(f"Error merging audio with video: {e}")
        return False 