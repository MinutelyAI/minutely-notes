# minutely-notes

AI-powered meeting transcription project for MinutelyAI.

This repository includes two browser-based experiences:

- `meeting.html`: live, multi-user transcription with shared real-time output
- `minutely.html`: upload a recorded audio/video file and get diarized transcription (speaker-labeled)

## What It Uses

- Deepgram WebSocket API for live speech-to-text
- Firebase Realtime Database for syncing live transcripts across participants
- Modal GPU endpoint for offline transcription
- Whisper `medium` + pyannote speaker diarization on the backend

## Project Files

- `meeting.html`: live meeting page
- `minutely.html`: recorded file transcription page
- `modal_app.py`: Modal backend (FastAPI + Whisper + pyannote)
- `config.example.js`: frontend config template
- `requirements.txt`: backend Python dependencies

## Prerequisites

You need:

- A Deepgram API key
- A Firebase project (Realtime Database enabled)
- A Hugging Face token with access to pyannote models
- A Modal account and CLI
- Python 3.11+ for local backend setup/deploy

## Quick Start

### 1. Configure Frontend Keys

Create `config.js` from the template:

```bash
cp config.example.js config.js
```

Then update:

- `DEEPGRAM_KEY`
- `MODAL_URL` (after deploying backend)
- `FIREBASE` object values

Important: `config.js` is gitignored and should never be committed.

### 2. Run Live Meeting Page

Open `meeting.html` in Chrome.

Flow:

1. Enter your name and create/join a meeting
2. Share the invite link
3. Each participant starts microphone capture
4. Transcript updates in real time for everyone

### 3. Run Recorded Transcription Page

Open `minutely.html` in a browser, upload one file, and click transcribe.

Supported formats include `.mp3`, `.wav`, `.mp4`, `.m4a`, `.webm`.

## Deploy Backend to Modal

Install dependencies and deploy:

```bash
pip install -r requirements.txt
modal secret create minutely-secrets HF_TOKEN=your_hf_token
modal deploy modal_app.py
```

Take the generated endpoint and set it as `MODAL_URL` in `config.js`.

## Backend API Contract

`POST /` expects JSON payload:

```json
{
	"audio": "<base64-audio-bytes>",
	"language": "en",
	"min_speakers": 1,
	"max_speakers": 8
}
```

Response includes:

- full transcript text
- detected language
- speaker segments with timestamps

## Troubleshooting

- If mic capture fails, verify browser mic permissions and use HTTPS when required.
- If live transcript is empty, confirm `DEEPGRAM_KEY` and Firebase config are valid.
- If recorded transcription fails, verify `MODAL_URL` and that Modal app is deployed.
- If diarization fails, verify `HF_TOKEN` is set in `minutely-secrets`.

## Security Notes

- Never commit `config.js`.
- Rotate any API key that was accidentally exposed.
- Restrict Firebase rules appropriately for production.
