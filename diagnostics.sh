#!/usr/bin/env bash
set -u

cd /home/vlados/pi_friend || exit 1

echo "== pi_friend diagnostics =="
echo "PWD: $PWD"
echo

echo "== Project files =="
for f in requirements.txt config.py main.py audio_input.py speech_to_text.py llm_client.py tts.py robot_face.py install.sh start.sh stop.sh; do
  if [ -f "$f" ]; then
    echo "OK $f"
  else
    echo "MISSING $f"
  fi
done
echo

echo "== Hailo =="
if [ -e /dev/hailo0 ]; then
  echo "OK /dev/hailo0 exists"
else
  echo "MISSING /dev/hailo0"
fi

if command -v hailortcli >/dev/null 2>&1; then
  hailortcli fw-control identify || true
else
  echo "hailortcli not found"
fi
echo

echo "== hailo-ollama =="
if pgrep -f "hailo-ollama serve" >/dev/null 2>&1; then
  echo "OK hailo-ollama serve is running"
else
  echo "hailo-ollama serve is not running"
fi

if [ -x /usr/bin/hailo-ollama ]; then
  echo "OK /usr/bin/hailo-ollama exists"
else
  echo "MISSING /usr/bin/hailo-ollama"
fi
echo

echo "== LLM chat test =="
if [ -x venv/bin/python ]; then
  venv/bin/python - <<'PY'
import time
import requests

payload = {
    "model": "qwen2.5-instruct:1.5b",
    "stream": False,
    "messages": [{"role": "user", "content": "Say ready."}],
}

try:
    start = time.time()
    r = requests.post("http://127.0.0.1:8000/api/chat", json=payload, timeout=12)
    elapsed = time.time() - start
    print("HTTP", r.status_code, "elapsed", round(elapsed, 2), "sec")
    print(r.text[:500])
except Exception as exc:
    print("LLM test failed:", exc)
PY
else
  echo "venv missing. Run ./install.sh first."
fi
echo

echo "== ALSA input devices =="
arecord -l || true
echo

echo "== ALSA output devices =="
aplay -l || true
echo

echo "== Python sounddevice devices =="
if [ -x venv/bin/python ]; then
  venv/bin/python - <<'PY'
try:
    import sounddevice as sd
    print(sd.query_devices())
except Exception as exc:
    print("sounddevice failed:", exc)
PY
else
  echo "venv missing"
fi
echo

echo "== Piper =="
if [ -x vendor/piper/piper ]; then
  echo "OK vendor/piper/piper"
else
  echo "MISSING vendor/piper/piper"
fi

if [ -f voices/en_US-lessac-medium.onnx ]; then
  echo "OK voices/en_US-lessac-medium.onnx"
else
  echo "MISSING voices/en_US-lessac-medium.onnx"
fi

if [ -x vendor/piper/piper ] && [ -f voices/en_US-lessac-medium.onnx ]; then
  echo "Generating /tmp/pi_friend_diag_tts.wav"
  echo "Hello, I am pi friend." | vendor/piper/piper --model voices/en_US-lessac-medium.onnx --output_file /tmp/pi_friend_diag_tts.wav || true
  if [ "${1:-}" = "--play" ]; then
    aplay -D plughw:CARD=UACDemoV10,DEV=0 /tmp/pi_friend_diag_tts.wav || true
  else
    echo "Run ./diagnostics.sh --play to also test speaker playback."
  fi
fi
echo

echo "== whisper.cpp =="
WHISPER_BIN=""
if [ -x vendor/whisper.cpp/build/bin/whisper-cli ]; then
  WHISPER_BIN="vendor/whisper.cpp/build/bin/whisper-cli"
elif [ -x vendor/whisper.cpp/build/bin/main ]; then
  WHISPER_BIN="vendor/whisper.cpp/build/bin/main"
fi

if [ -n "$WHISPER_BIN" ]; then
  echo "OK $WHISPER_BIN"
else
  echo "MISSING whisper.cpp binary"
fi

if [ -f models/ggml-base.en.bin ]; then
  echo "OK models/ggml-base.en.bin"
else
  echo "MISSING models/ggml-base.en.bin"
fi

if [ -n "$WHISPER_BIN" ] && [ -f models/ggml-base.en.bin ] && [ -f /tmp/pi_friend_diag_tts.wav ]; then
  echo "Transcribing Piper diagnostic WAV"
  "$WHISPER_BIN" -m models/ggml-base.en.bin -f /tmp/pi_friend_diag_tts.wav -l en -t 4 -nt || true
fi
echo

echo "== Config summary =="
if [ -x venv/bin/python ]; then
  venv/bin/python - <<'PY'
import config
print("MIC_DEVICE_INDEX =", config.MIC_DEVICE_INDEX)
print("MIC_SAMPLE_RATE =", config.MIC_SAMPLE_RATE)
print("AUDIO_OUTPUT_DEVICE =", config.AUDIO_OUTPUT_DEVICE)
print("ENABLE_GUI =", config.ENABLE_GUI)
print("ENABLE_WAKE_PHRASE =", config.ENABLE_WAKE_PHRASE)
print("ENABLE_CONVERSATION_MODE =", config.ENABLE_CONVERSATION_MODE)
print("LLM_MODEL =", config.LLM_MODEL)
PY
fi
