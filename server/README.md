# AI YouTube Shorts Generator

A Django API that takes a YouTube URL, automatically generates a vertical short highlight video, and saves the result locally (or to Cloudinary when configured).

## Features

- Extract the most engaging parts of a YouTube video using Anthropic Claude (Sonnet 4.6)
- Local transcription with Faster-Whisper (no external STT calls)
- Text-to-speech via Deepgram Aura (for dubbing flow)
- Automatically create a short vertical video format (9:16 aspect ratio)
- Save the generated shorts under `media/local/` and serve them via Django (Cloudinary upload is optional)
- Store processing metadata in SQLite (Supabase optional)
- Track processing status with a RESTful API

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd AI-Youtube-Shorts-Generator
```

2. Install the dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables in `.env`:
```
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key

# Required only for the dubbing flow (Deepgram Aura text-to-speech)
DEEPGRAM_API_KEY=your_deepgram_api_key

# Public origin used to build URLs for locally-stored media files
PUBLIC_BASE_URL=http://localhost:8000

# Optional: Cloudinary upload (leave blank for fully local mode)
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=

# Optional: Supabase mirror (leave blank for fully local mode)
SUPABASE_URL=
SUPABASE_KEY=
SUPABASE_TABLE=shorts
```

4. Run migrations:
```bash
python manage.py migrate
```

5. Start the server:
```bash
python manage.py runserver
```

## API Endpoints

### Create a Short

```
POST /api/shorts/
```

Request body:
```json
{
  "url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "username": "user_name"
}
```

Response:
```json
{
  "message": "Video processing started",
  "processing": {
    "id": 1,
    "username": "user_name",
    "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "status": "PENDING",
    "cloudinary_url": null,
    "created_at": "2023-06-15T10:30:00Z",
    "updated_at": "2023-06-15T10:30:00Z"
  }
}
```

### Check Processing Status

```
GET /api/shorts/status/{processing_id}/
```

Response:
```json
{
  "id": 1,
  "username": "user_name",
  "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "status": "COMPLETED",
  "cloudinary_url": "https://res.cloudinary.com/your-cloud/video/upload/v1234567890/shorts/final_1.mp4",
  "created_at": "2023-06-15T10:30:00Z",
  "updated_at": "2023-06-15T10:35:00Z"
}
```

### Get User's Videos

```
GET /api/shorts/user/{username}/
```

Response:
```json
[
  {
    "id": 1,
    "username": "user_name",
    "youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "status": "COMPLETED",
    "cloudinary_url": "https://res.cloudinary.com/your-cloud/video/upload/v1234567890/shorts/final_1.mp4",
    "created_at": "2023-06-15T10:30:00Z",
    "updated_at": "2023-06-15T10:35:00Z"
  },
  {
    "id": 2,
    "username": "user_name",
    "youtube_url": "https://www.youtube.com/watch?v=ANOTHER_VIDEO_ID",
    "status": "PROCESSING",
    "cloudinary_url": null,
    "created_at": "2023-06-15T11:30:00Z",
    "updated_at": "2023-06-15T11:30:00Z"
  }
]
```

## Supabase Database Structure

The Supabase database table `shorts` structure:

| Column       | Type      | Description                            |
|--------------|-----------|----------------------------------------|
| id           | integer   | Auto-incrementing primary key          |
| username     | text      | Username of the video owner            |
| youtube_url  | text      | Original YouTube video URL             |
| short_url    | text      | Cloudinary URL of the generated short  |
| created_at   | timestamp | Creation timestamp                     |

## Technology Stack

- Django & Django REST Framework
- Anthropic Claude (Sonnet 4.6) for highlight extraction and translation
- Deepgram Aura for text-to-speech
- Faster-Whisper (local) for transcription
- MoviePy for video editing
- OpenCV for face detection and tracking
- Local filesystem storage by default; optional Cloudinary for hosted video
- SQLite by default; optional Supabase mirror
- PyTube for YouTube video downloading
