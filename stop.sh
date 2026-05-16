#!/usr/bin/env bash
set -u

cd /home/vlados/pi_friend || exit 1

stop_pid_file() {
  pid_file="$1"
  label="$2"
  required_text="$3"

  if [ ! -f "$pid_file" ]; then
    echo "$label pid file not found."
    return
  fi

  pid="$(cat "$pid_file" 2>/dev/null || true)"
  if [ -z "$pid" ]; then
    echo "$label pid file is empty."
    rm -f "$pid_file"
    return
  fi

  if ! kill -0 "$pid" 2>/dev/null; then
    echo "$label is not running. Removing stale pid file."
    rm -f "$pid_file"
    return
  fi

  cmd="$(ps -p "$pid" -o command= 2>/dev/null || true)"
  case "$cmd" in
    *"$required_text"*|*"main.py"*|*"start.sh"*)
      echo "Stopping $label PID $pid"
      kill -INT "$pid" 2>/dev/null || true
      sleep 2

      if kill -0 "$pid" 2>/dev/null; then
        echo "$label still running; sending TERM"
        kill -TERM "$pid" 2>/dev/null || true
        sleep 2
      fi

      if kill -0 "$pid" 2>/dev/null; then
        echo "$label still running; sending KILL"
        kill -KILL "$pid" 2>/dev/null || true
        sleep 1
      fi

      rm -f "$pid_file"
      ;;
    *)
      echo "Refusing to stop PID $pid because it does not look like $label."
      echo "Command was: $cmd"
      ;;
  esac
}

stop_pid_file "logs/pi_friend.pid" "pi_friend" "/home/vlados/pi_friend"
stop_pid_file "logs/robot_face.pid" "robot_face" "robot_face.py"

if [ "${1:-}" = "--hailo-ollama" ]; then
  stop_pid_file "logs/hailo_ollama.pid" "hailo-ollama started by pi_friend" "hailo-ollama serve"
else
  echo "Leaving hailo-ollama running. Use ./stop.sh --hailo-ollama only if pi_friend started it and you want it stopped."
fi
