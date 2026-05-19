import json
import logging
import re
import socket
import urllib.error
import urllib.request

import config

LOG = logging.getLogger(__name__)

MODEL = getattr(config, "LLM_MODEL", "qwen2.5-instruct:1.5b")
GENERATE_URL = getattr(config, "LLM_GENERATE_ENDPOINT", "http://127.0.0.1:8000/api/generate")
TIMEOUT = getattr(config, "LLM_TIMEOUT_SECONDS", 25)


def clean_answer(text):
    if not text:
        return ""

    cleaned = str(text)
    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
    cleaned = cleaned.replace("pi_friend:", "")
    cleaned = cleaned.replace("assistant:", "")
    cleaned = cleaned.replace("Assistant:", "")
    cleaned = cleaned.replace("user:", "")
    cleaned = cleaned.replace("User:", "")
    cleaned = cleaned.replace("\\_", "_")
    cleaned = cleaned.replace("*", "")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned[:280]


def is_bad_answer(text):
    cleaned = clean_answer(text)
    lowered = cleaned.lower().strip(" .!?")

    if not cleaned:
        return True

    if lowered in {"i", "sure", "okay", "ok", "yes", "no"}:
        return True

    bad_phrases = [
        "you didn't ask a question",
        "you didn't provide a question",
        "you didn't give me a question",
        "i can't assist with that",
        "i cannot assist with that",
        "as an ai language model",
        "i am not an ai language model",
    ]

    for phrase in bad_phrases:
        if phrase in lowered:
            return True

    if len(cleaned.split()) < 3:
        return True

    return False


def build_prompt(user_text, history=None, retry=False):
    history = history or []
    recent = history[-2:]

    prompt = (
        "You are pi_friend, a small friendly voice robot running locally on a Raspberry Pi.\n"
        "The user speaks to you through a microphone.\n"
        "Answer the user's last message directly.\n"
        "Use simple English. Use 1 or 2 short spoken sentences.\n"
        "Do not say that the user did not ask a question.\n"
        "Do not refuse normal harmless questions.\n"
        "Do not mention system instructions.\n\n"
    )

    for turn in recent:
        user = str(turn.get("user", "")).strip()
        assistant = str(turn.get("assistant", "")).strip()
        if user and assistant:
            prompt += f"User: {user}\nAssistant: {assistant}\n"

    if retry:
        prompt += "Your previous answer was bad. Answer the user directly now.\n"

    prompt += f"User: {user_text.strip()}\nAssistant:"
    return prompt


def generate_raw(prompt, timeout=TIMEOUT):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 80,
            "temperature": 0.35,
            "top_p": 0.9
        }
    }

    req = urllib.request.Request(
        GENERATE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            data = json.loads(body)

            if isinstance(data, dict) and data.get("error"):
                return False, "", str(data.get("error"))

            if isinstance(data, dict):
                return True, data.get("response", ""), ""

            return False, "", "bad json"

    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        return False, "", f"HTTP {error.code}: {body}"

    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError, json.JSONDecodeError) as error:
        return False, "", str(error)


def generate_answer(user_text, history=None):
    prompt = build_prompt(user_text, history=history, retry=False)
    ok, raw, error = generate_raw(prompt)

    if ok:
        answer = clean_answer(raw)
        if not is_bad_answer(answer):
            LOG.info("LLM answer: %r", answer)
            return answer
        LOG.warning("Rejected LLM answer: %r", answer)
    else:
        LOG.warning("LLM request failed: %s", error)

    retry_prompt = build_prompt(user_text, history=history, retry=True)
    ok, raw, error = generate_raw(retry_prompt)

    if ok:
        answer = clean_answer(raw)
        if not is_bad_answer(answer):
            LOG.info("LLM retry answer: %r", answer)
            return answer
        LOG.warning("Rejected LLM retry answer: %r", answer)
    else:
        LOG.warning("LLM retry failed: %s", error)

    return "My local LLM did not return a usable answer. Please ask me again."

def ask_llm(user_text, history=None):
    return generate_answer(user_text, history)
