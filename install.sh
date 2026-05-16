#!/usr/bin/env bash
set -euo pipefail

cd /home/vlados/pi_friend

if [ "$PWD" != "/home/vlados/pi_friend" ]; then
  echo "Refusing to run outside /home/vlados/pi_friend"
  exit 1
fi

mkdir -p logs models voices vendor vendor/piper vendor/downloads

missing=()
for cmd in python3 git cmake make g++ curl tar arecord aplay; do
  if ! command -v "$cmd" >/dev/null 2>&1; then
    missing+=("$cmd")
  fi
done

if [ "${#missing[@]}" -gt 0 ]; then
  echo "Missing required commands: ${missing[*]}"
  echo
  echo "Ask before installing apt packages. Suggested packages:"
  echo "sudo apt install python3-venv git cmake build-essential curl alsa-utils libportaudio2 portaudio19-dev"
  exit 1
fi

if [ ! -d venv ]; then
  if ! python3 -m venv venv; then
    echo
    echo "Python venv creation failed."
    echo "Ask before installing apt packages. Suggested package:"
    echo "sudo apt install python3-venv"
    exit 1
  fi
fi

. venv/bin/activate
python -m pip install --upgrade pip wheel
python -m pip install -r requirements.txt

if ! python - <<'PY'
import numpy
import requests
import sounddevice
print("Python dependencies OK")
PY
then
  echo
  echo "Python dependency import failed."
  echo "If sounddevice complains about PortAudio, ask before installing:"
  echo "sudo apt install libportaudio2 portaudio19-dev"
  exit 1
fi

PIPER_URL="https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_aarch64.tar.gz"
PIPER_ARCHIVE="vendor/downloads/piper_linux_aarch64.tar.gz"

if [ ! -x vendor/piper/piper ]; then
  echo "Downloading fresh Piper..."
  curl -L --fail --retry 3 -o "$PIPER_ARCHIVE" "$PIPER_URL"
  tar -xzf "$PIPER_ARCHIVE" -C vendor/piper --strip-components=1
  chmod +x vendor/piper/piper
fi

if ! vendor/piper/piper --help >/dev/null 2>&1; then
  echo "Piper binary was downloaded but did not run on this system."
  echo "Do not copy old Piper files from any other project. Paste this error back."
  exit 1
fi

download_file() {
  url="$1"
  dest="$2"
  if [ -s "$dest" ]; then
    echo "Already present: $dest"
    return
  fi
  tmp="${dest}.part"
  curl -L --fail --retry 3 -o "$tmp" "$url"
  mv "$tmp" "$dest"
}

VOICE_ONNX_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx?download=true"
VOICE_JSON_URL="https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json?download=true"

echo "Downloading fresh Piper voice..."
download_file "$VOICE_ONNX_URL" "voices/en_US-lessac-medium.onnx"
download_file "$VOICE_JSON_URL" "voices/en_US-lessac-medium.onnx.json"

if [ ! -d vendor/whisper.cpp/.git ]; then
  if [ -e vendor/whisper.cpp ] && [ -n "$(find vendor/whisper.cpp -mindepth 1 -maxdepth 1 2>/dev/null | head -n 1)" ]; then
    echo "vendor/whisper.cpp exists but is not a fresh git clone."
    echo "Move it aside inside /home/vlados/pi_friend, then rerun ./install.sh"
    exit 1
  fi

  echo "Cloning fresh whisper.cpp..."
  git clone --depth 1 https://github.com/ggml-org/whisper.cpp.git vendor/whisper.cpp
fi

echo "Building whisper.cpp..."
JOBS="$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)"
cmake -S vendor/whisper.cpp -B vendor/whisper.cpp/build -DCMAKE_BUILD_TYPE=Release -DGGML_NATIVE=ON -DWHISPER_BUILD_TESTS=OFF
cmake --build vendor/whisper.cpp/build --config Release -j "$JOBS"

if [ -x vendor/whisper.cpp/build/bin/whisper-cli ]; then
  WHISPER_BIN="vendor/whisper.cpp/build/bin/whisper-cli"
elif [ -x vendor/whisper.cpp/build/bin/main ]; then
  WHISPER_BIN="vendor/whisper.cpp/build/bin/main"
else
  echo "whisper.cpp build finished, but no whisper-cli binary was found."
  exit 1
fi

WHISPER_MODEL_URL="https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin"
echo "Downloading Whisper base.en model..."
download_file "$WHISPER_MODEL_URL" "models/ggml-base.en.bin"

echo
echo "Install finished."
echo "Whisper binary: $WHISPER_BIN"
echo "Next: ./diagnostics.sh"
