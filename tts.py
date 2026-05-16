import logging
import subprocess
import time
from pathlib import Path

import config


def synthesize(text: str, output_path: Path = config.TTS_WAV_PATH) -> Path:
    text = text.strip()
    if not text:
        raise ValueError("No text to speak.")

    if not config.PIPER_BINARY.exists():
        raise FileNotFoundError(f"Piper binary not found: {config.PIPER_BINARY}")
    if not config.PIPER_VOICE_PATH.exists():
        raise FileNotFoundError(f"Piper voice not found: {config.PIPER_VOICE_PATH}")

    cmd = [
        str(config.PIPER_BINARY),
        "--model",
        str(config.PIPER_VOICE_PATH),
        "--output_file",
        str(output_path),
    ]

    logging.info("Running Piper TTS")
    result = subprocess.run(
        cmd,
        input=text + "\n",
        text=True,
        capture_output=True,
        timeout=config.PIPER_TIMEOUT_SECONDS,
    )

    if result.returncode != 0:
        stderr = result.stderr[-1200:] if result.stderr else "unknown Piper error"
        raise RuntimeError(stderr)

    return Path(output_path)


def play_wav(path: Path) -> None:
    cmd = [
        "aplay",
        "-q",
        "-D",
        config.AUDIO_OUTPUT_DEVICE,
        str(path),
    ]

    logging.info("Playing %s", path)
    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        timeout=config.APLAY_TIMEOUT_SECONDS,
    )

    if result.returncode != 0:
        stderr = result.stderr[-1200:] if result.stderr else "unknown aplay error"
        raise RuntimeError(stderr)


def speak(text: str) -> bool:
    wav_path = synthesize(text)
    play_wav(wav_path)
    time.sleep(config.SPEAK_COOLDOWN_SECONDS)
    return True
