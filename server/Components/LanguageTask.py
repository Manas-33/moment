import os
import json
import torch
import numpy as np
from transformers import AutoTokenizer, AutoModel
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
import re
from dotenv import load_dotenv

load_dotenv()

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


def parse_transcript(transcript_text):
    """
    Parses transcript text that includes timestamps.
    Expected format: 
    [00:01.23] Text goes here
    [00:05.67] More text here
    """
    segments = []

    pattern = r'\[(\d+:)?\d+:\d+\.\d+\]|\[(\d+:)?\d+:\d+\]'
    

    parts = re.split(pattern, transcript_text)
    timestamps = re.findall(pattern, transcript_text)
    

    time_in_seconds = []
    for ts in timestamps:
        ts = ts.strip('[]')
        parts = ts.split(':')
        if len(parts) == 3:  # HH:MM:SS
            hours, minutes, seconds = parts
            seconds_total = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        else:  # MM:SS
            minutes, seconds = parts
            seconds_total = int(minutes) * 60 + float(seconds)
        time_in_seconds.append(seconds_total)
    

    for i in range(len(time_in_seconds)):
        if i*2+1 < len(parts):  # Ensure we have text for this timestamp
            text = parts[i*2+1].strip()
            if text:  # Only add if there's actual text
                start_time = time_in_seconds[i]
                end_time = time_in_seconds[i+1] if i+1 < len(time_in_seconds) else start_time + 5  # Assume 5s if no next timestamp
                segments.append({
                    "start": start_time,
                    "text": text,
                    "end": end_time
                })
    
    return segments


def get_bert_embeddings(sentences, model_name='all-MiniLM-L6-v2'):

    model = SentenceTransformer(model_name)
    

    embeddings = model.encode(sentences, show_progress_bar=True)
    
    return embeddings


def extract_highlights_bert(transcript, min_duration=30, max_duration=60):

    segments = parse_transcript(transcript)
    
    if not segments:
        print("Failed to parse transcript or no segments found.")
        return 0, 0, ""
    

    sentences = [segment["text"] for segment in segments]
    
    if not sentences:
        print("No sentences extracted from transcript.")
        return 0, 0, ""
    

    embeddings = get_bert_embeddings(sentences)
    
    avg_embedding = np.mean(embeddings, axis=0)
    relevance_scores = cosine_similarity([avg_embedding], embeddings)[0]
    

    position_bonus = np.zeros(len(sentences))
    
    for i in range(len(sentences)):
        normalized_pos = i / len(sentences)
        position_bonus[i] = 1 - 2 * abs(normalized_pos - 0.5)
    
    length_scores = np.array([min(1.0, len(sentence.split()) / 10) for sentence in sentences])
    

    final_scores = 0.7 * relevance_scores + 0.2 * position_bonus + 0.1 * length_scores
    

    best_start_idx = 0
    best_end_idx = 0
    best_score = 0
    
    for start_idx in range(len(segments)):
        current_duration = 0
        current_score = 0
        
        for end_idx in range(start_idx, len(segments)):
            segment_duration = segments[end_idx]["end"] - segments[start_idx]["start"]
            
            if segment_duration < min_duration:

                current_score += final_scores[end_idx]
                continue
                
            if segment_duration > max_duration:

                break
                

            segment_score = sum(final_scores[start_idx:end_idx+1]) / (end_idx - start_idx + 1)
            
            if segment_score > best_score:
                best_score = segment_score
                best_start_idx = start_idx
                best_end_idx = end_idx
    
    if best_start_idx == best_end_idx and best_score == 0:
        print("Could not find a suitable highlight segment.")
        return 0, 0, ""
    

    start_time = segments[best_start_idx]["start"]
    end_time = segments[best_end_idx]["end"]
    highlight_text = " ".join([segments[i]["text"] for i in range(best_start_idx, best_end_idx + 1)])
    

    result = [{
        "start": str(start_time),
        "content": highlight_text,
        "end": str(end_time)
    }]
    
    return int(start_time), int(end_time), json.dumps(result, indent=2)

def GetHighlight(transcript):
    print("Getting Highlight from Transcript using BERT")
    try:

        start, end, json_string = extract_highlights_bert(transcript)
        
        if start == end or start == 0:
            ask = input("Error - Get Highlights again (y/n) -> ").lower()
            if ask == "y":
                start, end, _ = extract_highlights_bert(transcript)
        
        print(f"Selected highlight: {json_string}")
        return start, end

    except Exception as e:
        print(f"Error in GetHighlight: {e}")
        return 0, 0

# if __name__ == "__main__":

#     example_transcript = """
#     [00:00.00] Welcome to our tutorial on machine learning.
#     [00:05.25] Today we'll discuss the fundamentals of neural networks.
#     [00:10.50] Neural networks are composed of layers of interconnected nodes.
#     [00:15.75] Each node performs a simple mathematical operation.
#     [00:20.00] When combined, these operations can model complex patterns.
#     [00:25.50] The most exciting application is in computer vision.
#     [00:30.75] For example, self-driving cars use neural networks to identify objects.
#     [00:36.00] Another fascinating use case is natural language processing.
#     [00:42.25] This allows computers to understand and generate human language.
#     [00:48.50] The future of AI depends on advancements in neural network architectures.
#     """
    
#     start, end = GetHighlight(example_transcript)
#     print(f"Highlight segment: {start}s to {end}s")