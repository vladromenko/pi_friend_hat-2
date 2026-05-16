import logging
import re
import signal
import sys
import time

import audio_input
import config
import llm_client
import speech_to_text
import tts
from robot_face import FaceController

RUNNING = True


def setup_logging() -> None:
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.FileHandler(config.LOG_DIR / "pi_friend.log", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def handle_signal(signum, frame) -> None:
    global RUNNING
    RUNNING = False
    logging.info("Signal received: %s", signum)


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-zа-яё0-9\s]+", " ", text, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", text).strip()


def is_sleep_phrase(text: str) -> bool:
    normalized = normalize_text(text)
    return normalized in config.SLEEP_PHRASES


def limited_history(history: list[dict]) -> list[dict]:
    return history[-config.MAX_HISTORY_TURNS * 2:]


def run_one_turn(face: FaceController, history: list[dict] | None = None, skip_quiet: bool = False) -> tuple[str, str] | None:
    try:
        face.set_state("listening")
        wav_path, rms = audio_input.record_wav()

        if skip_quiet and rms < config.MIN_RECORD_RMS:
            face.set_state("idle")
            logging.info("Skipping quiet input rms=%.5f", rms)
            return None

        face.set_state("thinking")
        transcript = speech_to_text.transcribe_wav(wav_path)
        if not transcript:
            face.set_state("idle")
            return None

        print(f"You: {transcript}")

        answer = llm_client.ask_llm(transcript, limited_history(history or []))
        print(f"pi_friend: {answer}")

        face.set_state("speaking")
        tts.speak(answer)
        face.set_state("idle")

        return transcript, answer

    except KeyboardInterrupt:
        raise
    except Exception as exc:
        logging.exception("Turn failed")
        print(f"pi_friend error: {exc}")
        face.set_state("idle")
        time.sleep(1.0)
        return None


def run_enter_mode(face: FaceController) -> None:
    print("pi_friend Stage 1 is ready.")
    print("Press Enter to record 4 seconds. Press Ctrl+C to stop.")
    history: list[dict] = []

    while RUNNING:
        try:
            input("\nPress Enter to talk: ")
        except EOFError:
            break

        result = run_one_turn(face, history, skip_quiet=False)
        if result:
            user_text, answer = result
            history.extend([
                {"role": "user", "content": user_text},
                {"role": "assistant", "content": answer},
            ])


def run_auto_mode(face: FaceController) -> None:
    print("pi_friend auto-listening mode is ready.")
    print("Speak naturally. It listens in short 4-second turns. Press Ctrl+C to stop.")
    history: list[dict] = []

    while RUNNING:
        result = run_one_turn(face, history, skip_quiet=True)
        if not result:
            continue

        user_text, answer = result
        if is_sleep_phrase(user_text):
            print("Sleep phrase heard. Pausing briefly.")
            time.sleep(5)
            continue

        history.extend([
            {"role": "user", "content": user_text},
            {"role": "assistant", "content": answer},
        ])


def main() -> None:
    setup_logging()
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    face = FaceController(enabled=config.ENABLE_GUI)
    face.start()

    try:
        face.set_state("idle")
        if config.ENABLE_CONVERSATION_MODE:
            run_auto_mode(face)
        else:
            run_enter_mode(face)
    finally:
        face.stop()
        logging.info("pi_friend stopped")


if __name__ == "__main__":
    main()
