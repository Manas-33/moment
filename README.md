# Highlightr - AI-Powered Video Content Creator

Transform your long-form videos and podcasts into engaging short clips using AI. Automatically generate captions, translate content, and create viral-ready content for social media.

## Features

- 🎥 **AI Video Processing**: Convert long videos into multiple short clips
- 🗣️ **Language Dubbing**: Translate and dub videos in multiple languages
- 📝 **Auto Captions**: Generate and customize captions automatically
- ☁️ **Cloud Storage**: Integrated with Cloudinary for video hosting
- 🔐 **User Authentication**: Secure login with Supabase Auth
- 📱 **Responsive UI**: Modern, mobile-friendly interface

## Tech Stack

**Frontend:**
- Next.js 15 with TypeScript
- Tailwind CSS + shadcn/ui components
- Supabase for authentication
- Framer Motion for animations

**Backend:**
- Django REST Framework
- Anthropic Claude (Sonnet 4.6) for highlight extraction and translation
- Deepgram Aura for text-to-speech
- Faster-Whisper (local) for transcription
- Local filesystem (or Cloudinary, optional) for video storage
- SQLite (or Supabase, optional) for database

## Quick Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.10+ (3.12 recommended)
- ffmpeg (`brew install ffmpeg` on macOS)
- Anthropic API key (`ANTHROPIC_API_KEY`)
- Deepgram API key (`DEEPGRAM_API_KEY`) — only required if you use the dubbing/translation flow
- Cloudinary / Supabase accounts are *optional* — by default everything runs locally

### 1. Clone the Repository
```bash
git clone https://github.com/Manas-33/Highlightr.git
cd Highlightr
```

### 2. Client Setup
```bash
cd client
npm install
```

No `.env.local` is required for local mode — the dashboard is the landing page (`http://localhost:3000`) and there is no login. If you later want Supabase auth back, add:
```env
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
```

Start development server:
```bash
npm run dev
```

### 3. Server Setup
```bash
cd server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create `server/.env`:
```env
# Required
ANTHROPIC_API_KEY=your_anthropic_api_key

# Required only for the dubbing/translation flow (text-to-speech)
DEEPGRAM_API_KEY=your_deepgram_api_key

# Optional — leave blank to keep everything local
CLOUDINARY_CLOUD_NAME=
CLOUDINARY_API_KEY=
CLOUDINARY_API_SECRET=
SUPABASE_URL=
SUPABASE_KEY=

# Optional Django basics
DEBUG=True
SECRET_KEY=any-string
# Public origin used for local media URLs returned by the API
PUBLIC_BASE_URL=http://localhost:8000
```

Run migrations and start server:
```bash
python manage.py migrate
python manage.py runserver
```

### 4. Database Setup (Optional - Supabase)

For production or if you prefer Supabase over SQLite:

1. Create tables in Supabase using the schema in `server/supabase_migrations/`
2. Set `USE_SUPABASE=True` in your server `.env`


## Usage

1. Open `http://localhost:3000` — you land directly on the dashboard (no login).
2. **Paste a YouTube URL** in the form.
3. **Select number of clips** to generate.
4. **Choose language** for dubbing (optional).
5. Generated clips appear in the dashboard and are stored under `server/media/local/`.


## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details.
 