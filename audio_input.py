import logging
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd

import config


def record_wav(
    path: Path = config.INPUT_WAV_PATH,
    duration: float = config.RECORD_SECONDS,
    sample_rate: int = config.MIC_SAMPLE_RATE,
    channels: int = config.MIC_CHANNELS,
    device_index: int = config.MIC_DEVICE_INDEX,
) -> tuple[Path, float]:
    path = Path(path)
    frames = int(duration * sample_rate)

    logging.info("Recording %.1fs from mic index %s", duration, device_index)
    audio = sd.rec(
        frames,
        samplerate=sample_rate,
        channels=channels,
        dtype="int16",
        device=device_index,
    )
    sd.wait()

    data = np.asarray(audio)
    rms = 0.0
    if data.size:
        normalized = data.astype(np.float32) / 32768.0
        rms = float(np.sqrt(np.mean(normalized * normalized)))

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(data.tobytes())

    logging.info("Saved %s rms=%.5f", path, rms)
    return path, rms


def list_sound_devices() -> str:
    return str(sd.query_devices())
