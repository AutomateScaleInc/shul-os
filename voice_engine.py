#!/usr/bin/env python3
"""
Torah Sanctuary — Local Offline Neural Voice Engine (TTS + STT).
- TTS: Piper Neural Voice (en_US-joe-medium / en_US-ryan-high) + studio ffmpeg
  bass-baritone vocal mastering chain ("Grand Torah Narrator" deep resonant timbre).
- STT: 100% offline local Whisper transcription via Sentinel's `voxtype transcribe`
  (ggml-base.en.bin) + ffmpeg resampling from browser MediaRecorder audio.
"""

import os
import pathlib
import re
import subprocess
import tempfile

BASE_DIR = pathlib.Path(__file__).resolve().parent
VOICE_DIR = BASE_DIR / "voice"
PIPER_BIN = VOICE_DIR / "piper" / "piper"
MODELS_DIR = VOICE_DIR / "models"

VOICE_PROFILES = {
    "grand_narrator": {
        "label": "Grand Torah Narrator (Warm Natural Baritone)",
        "model": "en_US-ryan-high.onnx",
        "length_scale": "1.08",
        "sentence_silence": "0.38",
        "af": (
            "asetrate=22050*0.94,aresample=22050,atempo=1.04,"
            "equalizer=f=120:t=q:w=1.3:g=2.2,"
            "equalizer=f=240:t=q:w=1.5:g=1.2,"
            "highshelf=f=6500:g=-1.5,"
            "acompressor=threshold=-18dB:ratio=2.0:attack=15:release=120,"
            "volume=0.78"
        ),
    },
    "warm_baritone": {
        "label": "Deep Joe Baritone (Gentle)",
        "model": "en_US-joe-medium.onnx",
        "length_scale": "1.06",
        "sentence_silence": "0.36",
        "af": (
            "asetrate=22050*0.96,aresample=22050,atempo=1.03,"
            "equalizer=f=130:t=q:w=1.4:g=1.8,"
            "highshelf=f=6500:g=-1.5,"
            "volume=0.78"
        ),
    },
    "storyteller": {
        "label": "Gentle Family Storyteller (Natural)",
        "model": "en_US-ryan-high.onnx",
        "length_scale": "1.02",
        "sentence_silence": "0.34",
        "af": "equalizer=f=140:t=q:w=1.4:g=1.5,volume=0.78",
    },
}

HEBREW_RE = re.compile(r"[\u0590-\u05FF\uFB1D-\uFB4F]+")
VERSE_NUM_RE = re.compile(r"\b(\d{1,3}):(\d{1,3})(?:-(\d{1,3}))?\b")
URL_RE = re.compile(r"https?://\S+")


def clean_for_speech(text: str) -> str:
    s = str(text or "")
    s = URL_RE.sub("", s)
    # Remove markdown formatting & symbols
    s = re.sub(r"[#*_`~>|]", " ", s)
    # Remove raw Hebrew script from English TTS stream so English neural voice flows smoothly
    s = HEBREW_RE.sub(" ", s)
    # Natural spoken Torah verse citations: "Genesis 1:1-3" -> "Genesis chapter 1, verses 1 through 3"
    def _fmt_ref(m):
        if m.group(3):
            return f"chapter {m.group(1)}, verses {m.group(2)} through {m.group(3)}"
        return f"chapter {m.group(1)}, verse {m.group(2)}"
    s = VERSE_NUM_RE.sub(_fmt_ref, s)
    # Replace decorative glyphs/bullets with gentle pauses
    s = re.sub(r"[✡🕯📖📜✨💡✦❖📅📍🔊🎙⏸▶◀]+", " ", s)
    s = s.replace("—", ", ").replace("·", ", ").replace("()", "").replace("( )", "")
    s = re.sub(r"\(\s*[,;\s]*\)", "", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:2600]


def voice_status() -> dict:
    piper_ok = PIPER_BIN.exists() and os.access(PIPER_BIN, os.X_OK)
    avail = {}
    for k, prof in VOICE_PROFILES.items():
        mp = MODELS_DIR / prof["model"]
        avail[k] = {"label": prof["label"], "ready": bool(piper_ok and mp.exists())}
    vox_ok = pathlib.Path("/usr/bin/voxtype").exists()
    return {
        "tts_engine": "piper_neural" if piper_ok else "espeak_fallback",
        "piper_ready": piper_ok,
        "profiles": avail,
        "stt_engine": "voxtype_whisper_local" if vox_ok else "browser_only",
        "stt_ready": vox_ok,
    }


def synthesize_wav(text: str, profile: str = "grand_narrator") -> bytes:
    spoken = clean_for_speech(text)
    if not spoken:
        raise ValueError("Nothing speakable in text")

    prof = VOICE_PROFILES.get(profile) or VOICE_PROFILES["grand_narrator"]
    model_path = MODELS_DIR / prof["model"]

    with tempfile.TemporaryDirectory(prefix="torah_tts_") as td:
        raw_wav = os.path.join(td, "raw.wav")
        out_wav = os.path.join(td, "out.wav")

        if PIPER_BIN.exists() and model_path.exists():
            subprocess.run(
                [
                    str(PIPER_BIN),
                    "--model", str(model_path),
                    "--length_scale", prof["length_scale"],
                    "--sentence_silence", prof["sentence_silence"],
                    "--output_file", raw_wav,
                ],
                input=(spoken + "\n").encode("utf-8"),
                timeout=30,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True,
            )
            # Apply studio bass-baritone mastering chain via ffmpeg
            res_ff = subprocess.run(
                ["ffmpeg", "-y", "-i", raw_wav, "-af", prof["af"], out_wav],
                timeout=20,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            final_path = out_wav if (res_ff.returncode == 0 and os.path.exists(out_wav)) else raw_wav
            return pathlib.Path(final_path).read_bytes()

        # Fallback if Piper not installed
        subprocess.run(
            ["espeak-ng", "-s", "135", "-p", "28", "-w", out_wav, spoken],
            timeout=15,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        return pathlib.Path(out_wav).read_bytes()


def transcribe_audio(raw_audio: bytes, suffix: str = ".webm") -> str:
    """Convert browser microphone recording to 16kHz mono WAV and transcribe 100% offline with local Whisper."""
    if not raw_audio or len(raw_audio) < 400:
        return ""
    with tempfile.TemporaryDirectory(prefix="torah_stt_") as td:
        in_path = os.path.join(td, "input" + (suffix if suffix.startswith(".") else ".webm"))
        wav_path = os.path.join(td, "speech_16k.wav")
        pathlib.Path(in_path).write_bytes(raw_audio)
        subprocess.run(
            ["ffmpeg", "-y", "-i", in_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", wav_path],
            timeout=15,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )
        proc = subprocess.run(
            ["voxtype", "transcribe", wav_path],
            timeout=35,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        ansi_re = re.compile(r"\x1b\[[0-9;]*m")
        out_lines = []
        for line in proc.stdout.decode("utf-8", "ignore").splitlines():
            s = ansi_re.sub("", line).strip()
            if not s:
                continue
            # Filter out voxtype/whisper.cpp diagnostic lines
            if (
                re.match(r"^\d{4}-\d{2}-\d{2}T", s)
                or " INFO " in s
                or " WARN " in s
                or s.startswith("whisper_")
                or s.startswith("Loading audio file:")
                or s.startswith("Audio format:")
                or s.startswith("Processing ")
            ):
                continue
            out_lines.append(s)
        text = " ".join(out_lines).strip()
        # Strip bracketed noise tokens like [BLANK_AUDIO]
        text = re.sub(r"\[[^\]]*\]", "", text).strip()
        return text
