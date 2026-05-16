import logging
import re
import subprocess
from pathlib import Path

import config


def _find_whisper_binary() -> Path:
    candidates = [
        config.WHISPER_BINARY,
        config.VENDOR_DIR / "whisper.cpp" / "build" / "bin" / "main",
        config.VENDOR_DIR / "whisper.cpp" / "main",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    raise FileNotFoundError("whisper.cpp binary not found. Run ./install.sh first.")


def clean_transcript(raw: str) -> str:
    text = raw.replace("\r", "\n")
    lines = []

    for line in text.splitlines():
        s = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
        if not s:
            continue
        if s.startswith(("whisper_", "ggml_", "main:", "system_info:", "sampling:")):
            continue
        s = re.sub(r"^\[[0-9:.,\s\-]+-->\s*[0-9:.,\s\-]+\]\s*", "", s)
        lines.append(s)

    text = " ".join(lines)
    text = re.sub(r"\[[^\]]+\]", " ", text)
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" .,!?;:").strip()

    lower = text.lower()
    if lower in config.COMMON_EMPTY_TRANSCRIPTS:
        return ""
    if len(lower) <= 2 and lower not in {"hi"}:
        return ""

    return text


def transcribe_wav(wav_path: Path) -> str:
    binary = _find_whisper_binary()
    model = config.WHISPER_MODEL_PATH

    if not model.exists():
        raise FileNotFoundError(f"Whisper model not found: {model}")

    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    output_base = config.WHISPER_TEXT_BASE
    output_txt = output_base.with_suffix(".txt")
    if output_txt.exists():
        output_txt.unlink()

    cmd = [
        str(binary),
        "-m",
        str(model),
        "-f",
        str(wav_path),
        "-l",
        config.WHISPER_LANGUAGE,
        "-t",
        str(config.WHISPER_THREADS),
        "-nt",
        "-otxt",
        "-of",
        str(output_base),
    ]

    logging.info("Running whisper.cpp")
    result = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        timeout=config.WHISPER_TIMEOUT_SECONDS,
    )

    raw = ""
    if output_txt.exists():
        raw = output_txt.read_text(encoding="utf-8", errors="replace")
    if not raw.strip():
        raw = result.stdout

    if result.returncode != 0 and not raw.strip():
        stderr = result.stderr[-1200:] if result.stderr else "unknown whisper.cpp error"
        raise RuntimeError(stderr)

    transcript = clean_transcript(raw)
    logging.info("Transcript: %r", transcript)
    return transcript
