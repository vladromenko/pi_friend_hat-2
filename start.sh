#!/usr/bin/env bash
set -euo pipefail

cd /home/vlados/pi_friend
mkdir -p logs

PID_FILE="logs/pi_friend.pid"

cleanup() {
  status=$?
  trap - EXIT INT TERM
  if [ -f "$PID_FILE" ]; then
    saved_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
    if [ "$saved_pid" = "$$" ]; then
      rm -f "$PID_FILE"
    fi
  fi
  exit "$status"
}

trap cleanup EXIT INT TERM

if grep -q '^ENABLE_GUI = True' config.py; then
  if [ -z "${DISPLAY:-}" ]; then
    if [ -S /tmp/.X11-unix/X0 ]; then
      export DISPLAY=:0
      echo "Using local Raspberry Pi display: DISPLAY=:0"
    else
      echo "GUI is enabled, but no local X display socket was found."
      echo "Voice mode will still run; robot face may not open."
    fi
  fi

  if [ -z "${XAUTHORITY:-}" ] && [ -f "$HOME/.Xauthority" ]; then
    export XAUTHORITY="$HOME/.Xauthority"
  fi
fi

if [ -f "$PID_FILE" ]; then
  old_pid="$(cat "$PID_FILE" 2>/dev/null || true)"
  old_cmd="$(ps -p "$old_pid" -o command= 2>/dev/null || true)"
  if [ -n "$old_cmd" ]; then
    echo "Stopping old pi_friend PID $old_pid"
    kill -TERM "$old_pid" 2>/dev/null || true
    sleep 1
    kill -KILL "$old_pid" 2>/dev/null || true
  fi
  rm -f "$PID_FILE"
fi

if [ ! -x venv/bin/python ]; then
  echo "venv is missing. Run ./install.sh first."
  exit 1
fi

echo "Restarting hailo-ollama for a clean session..."
old_hailo="$(pgrep -f '^[h]ailo-ollama serve$' | head -n 1 || true)"
if [ -n "$old_hailo" ]; then
  kill "$old_hailo" 2>/dev/null || true
  sleep 5
fi

nohup hailo-ollama serve > /tmp/pi_friend_hailo_ollama.log 2>&1 &
echo "$!" > logs/hailo_ollama.pid

if ! venv/bin/python warmup_llm.py; then
  echo
  echo "LLM did not warm up correctly. Last hailo-ollama log lines:"
  tail -n 80 /tmp/pi_friend_hailo_ollama.log || true
  exit 1
fi

echo "$$" > "$PID_FILE"
venv/bin/python main.py
