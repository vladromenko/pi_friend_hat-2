from pathlib import Path

PROJECT_NAME = "pi_friend"
BASE_DIR = Path(__file__).resolve().parent

VENDOR_DIR = BASE_DIR / "vendor"
MODELS_DIR = BASE_DIR / "models"
VOICES_DIR = BASE_DIR / "voices"
LOG_DIR = BASE_DIR / "logs"

INPUT_WAV_PATH = Path("/tmp/pi_friend_input.wav")
TTS_WAV_PATH = Path("/tmp/pi_friend_tts.wav")
WHISPER_TEXT_BASE = LOG_DIR / "whisper_last"
FACE_STATE_FILE = LOG_DIR / "face_state.json"

MIC_DEVICE_INDEX = 2
MIC_SAMPLE_RATE = 44100
MIC_CHANNELS = 1
RECORD_SECONDS = 4.0
WAKE_RECORD_SECONDS = 2.5
MIN_RECORD_RMS = 0.012

AUDIO_OUTPUT_DEVICE = "plughw:CARD=UACDemoV10,DEV=0"
SPEAK_COOLDOWN_SECONDS = 0.8

PIPER_BINARY = VENDOR_DIR / "piper" / "piper"
PIPER_VOICE_PATH = VOICES_DIR / "en_US-lessac-medium.onnx"
PIPER_TIMEOUT_SECONDS = 25
APLAY_TIMEOUT_SECONDS = 20

WHISPER_BINARY = VENDOR_DIR / "whisper.cpp" / "build" / "bin" / "whisper-cli"
WHISPER_MODEL_PATH = MODELS_DIR / "ggml-base.en.bin"
WHISPER_LANGUAGE = "en"
WHISPER_THREADS = 4
WHISPER_TIMEOUT_SECONDS = 35

LLM_ENDPOINT = "http://127.0.0.1:8000/api/chat"
LLM_MODEL = "qwen2.5-instruct:1.5b"
LLM_TIMEOUT_SECONDS = 30
LLM_OPTIONS = {
    "temperature": 0.0,
    "top_p": 0.8,
    "num_predict": 32,
    "repeat_penalty": 1.25,
}

ASSISTANT_SYSTEM_PROMPT = (
    "You are pi_friend. "
    "Answer directly in one short sentence. "
    "Be friendly, but do not roleplay sounds or repeat words."
)

MAX_ANSWER_CHARS = 220
MAX_HISTORY_TURNS = 2

ENABLE_GUI = True
ENABLE_WAKE_PHRASE = False
ENABLE_CONVERSATION_MODE = True

WAKE_PHRASES = {
    "хай",
    "hi",
    "hey",
    "hai",
    "high",
    "hiya",
}

SLEEP_PHRASES = {
    "sleep",
    "go to sleep",
    "stop listening",
    "good night",
}

CONVERSATION_IDLE_TIMEOUT_SECONDS = 35

COMMON_EMPTY_TRANSCRIPTS = {
    "",
    ".",
    "..",
    "...",
    "you",
    "thank you",
    "thanks",
    "thanks for watching",
    "bye",
    "music",
}
