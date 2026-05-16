import json
import sys
import time
import urllib.request

import config


def post_json(url, payload, timeout):
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


def get_json(url, timeout):
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))


base = config.LLM_ENDPOINT.replace("/api/chat", "")
tags_url = base + "/api/tags"
generate_url = base + "/api/generate"

print("Waiting for hailo-ollama HTTP API...")
for attempt in range(1, 31):
    try:
        tags = get_json(tags_url, timeout=5)
        names = [m.get("name") for m in tags.get("models", [])]
        if config.LLM_MODEL in names:
            print(f"Model visible: {config.LLM_MODEL}")
            break
        print(f"Model list does not include {config.LLM_MODEL}: {names}")
    except Exception as exc:
        print(f"API not ready yet ({attempt}/30): {exc}")
    time.sleep(2)
else:
    print("hailo-ollama API did not become ready.", file=sys.stderr)
    sys.exit(1)

payload = {
    "model": config.LLM_MODEL,
    "stream": False,
    "prompt": "Answer with one word: ready",
    "options": {
        "num_predict": 4,
        "temperature": 0,
    },
}

print("Warming up LLM model. First boot can take up to 2 minutes...")
for attempt in range(1, 4):
    try:
        start = time.time()
        data = post_json(generate_url, payload, timeout=120)
        elapsed = time.time() - start
        text = (data.get("response") or "").strip()
        print(f"LLM warm-up OK in {elapsed:.1f}s: {text!r}")
        sys.exit(0)
    except Exception as exc:
        print(f"Warm-up failed ({attempt}/3): {exc}")
        time.sleep(5)

print("LLM warm-up failed.", file=sys.stderr)
sys.exit(1)
