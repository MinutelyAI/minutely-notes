import modal
import io

app = modal.App("minutely-notes")

# Persistent volume for model cache
volume = modal.Volume.from_name("minutely-model-cache", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg")
    .pip_install(
        "openai-whisper",
        "pyannote.audio",
        "fastapi",
        "uvicorn",
        "python-multipart",
        "python-dotenv",
        "soundfile",
        "numpy",
    )
)

@app.function(
    image=image,
    gpu="T4",
    timeout=600,
    secrets=[modal.Secret.from_name("minutely-secrets")],
    volumes={"/cache": volume},  # mount volume
)
def transcribe(audio_bytes: bytes, language: str = "en", min_speakers: int = 1, max_speakers: int = 8) -> dict:
    import whisper
    import torch
    import soundfile as sf
    import tempfile
    import os
    from pyannote.audio import Pipeline
    from concurrent.futures import ThreadPoolExecutor

    # Point model caches to persistent volume
    os.environ["WHISPER_CACHE"] = "/cache/whisper"
    os.environ["HF_HOME"] = "/cache/huggingface"
    os.makedirs("/cache/whisper", exist_ok=True)
    os.makedirs("/cache/huggingface", exist_ok=True)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🚀 Using device: {device}")

    whisper_model = whisper.load_model("medium", download_root="/cache/whisper")
    diarize_pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-3.1",
        token=os.environ["HF_TOKEN"]
    ).to(device)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    wav_path = tmp_path + ".wav"
    os.system(f"ffmpeg -i {tmp_path} -ar 16000 -ac 1 -y {wav_path}")

    audio_np = whisper.load_audio(wav_path)
    waveform_sf, sample_rate = sf.read(wav_path, dtype="float32")
    waveform_tensor = torch.tensor(waveform_sf).unsqueeze(0)
    audio_input = {"waveform": waveform_tensor, "sample_rate": sample_rate}

    with ThreadPoolExecutor() as executor:
        whisper_future = executor.submit(
            whisper_model.transcribe, audio_np,
            word_timestamps=True,
            language=language,
            condition_on_previous_text=False,
            temperature=0.0
        )
        diarize_future = executor.submit(
            diarize_pipeline, audio_input,
            min_speakers=min_speakers,
            max_speakers=max_speakers
        )
        whisper_result = whisper_future.result()
        diarization = diarize_future.result()

    def get_speaker(start, end):
        max_overlap = 0
        best_speaker = None
        for segment, _, speaker in diarization.speaker_diarization.itertracks(yield_label=True):
            overlap = min(end, segment.end) - max(start, segment.start)
            if overlap > max_overlap:
                max_overlap = overlap
                best_speaker = speaker
        return best_speaker

    raw = []
    for seg in whisper_result["segments"]:
        for word in seg.get("words", []):
            raw.append({
                "speaker": get_speaker(word["start"], word["end"]),
                "start": word["start"],
                "end": word["end"],
                "text": word["word"]
            })

    for i, w in enumerate(raw):
        if w["speaker"] is None:
            prev = next((raw[j]["speaker"] for j in range(i-1, -1, -1) if raw[j]["speaker"]), None)
            nxt = next((raw[j]["speaker"] for j in range(i+1, len(raw)) if raw[j]["speaker"]), None)
            w["speaker"] = prev or nxt or "UNKNOWN"

    segments = []
    for w in raw:
        if segments and segments[-1]["speaker"] == w["speaker"]:
            segments[-1]["end"] = round(w["end"], 2)
            segments[-1]["text"] += w["text"]
        else:
            segments.append({
                "speaker": w["speaker"],
                "start": round(w["start"], 2),
                "end": round(w["end"], 2),
                "text": w["text"]
            })

    for seg in segments:
        seg["text"] = seg["text"].strip()

    os.remove(tmp_path)
    os.remove(wav_path)

    return {
        "transcript": whisper_result["text"].strip(),
        "language": whisper_result["language"],
        "segments": segments
    }


@app.local_entrypoint()
def main():
    with open("meet1.mp3", "rb") as f:
        audio_bytes = f.read()
    result = transcribe.remote(audio_bytes)
    import json
    with open("transcript_modal.json", "w") as f:
        json.dump(result, f, indent=2)
    print("✅ Done! Check transcript_modal.json")