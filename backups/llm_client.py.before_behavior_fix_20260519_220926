import logging
import random
import re
from typing import Iterable

import requests

import config


FALLBACKS = [
    "Sorry, my local brain glitched for a second. Try that again.",
    "I missed that one; say it once more and I will try again.",
    "My thoughts tripped for a moment, but I am still here.",
]

FORBIDDEN = [
    "machine learning model",
    "language model",
    "ai model",
    "as an ai",
    "not a robot companion",
]


def _local_reply(user_text: str) -> str | None:
    text = user_text.lower().strip()

    if any(x in text for x in ["i'm tired", "i am tired", "im tired", "i feel tired", "tired"]):
        return random.choice([
            "That sounds rough; take a small pause, drink some water, and I will keep you company.",
            "I hear you. Let us slow down for a minute.",
            "Then let us make things easy for a bit; I am right here.",
        ])

    if text in {"hi", "hey", "hello"} or "how are you" in text:
        return random.choice([
            "Hi, I am here and ready.",
            "Hey, friend. I am glad to hear you.",
            "Hello. What shall we do next?",
        ])

    if "who are you" in text or "what is your name" in text:
        return random.choice([
            "I am pi_friend, your little robot companion.",
            "I am pi_friend, a small local robot friend on your Raspberry Pi.",
            "I am pi_friend, here to listen and help.",
        ])

    if "tell me a joke" in text or text == "joke":
        return random.choice([
            "Why did the computer get cold? Because it left its Windows open.",
            "Why did the robot bring a ladder? It wanted to reach the cloud.",
            "Why did the tiny robot stay calm? It had well-grounded circuits.",
        ])

    return None


def _looks_repetitive(answer: str) -> bool:
    words = re.findall(r"[0-9A-Za-zА-Яа-яЁё']+", answer.lower())
    if len(words) < 16:
        return False
    return len(set(words)) / len(words) < 0.45


def _clean_answer(answer: str, user_text: str) -> str:
    answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.DOTALL | re.IGNORECASE)
    answer = answer.replace("Assistant:", "").replace("pi_friend:", "").replace("User:", "")
    answer = re.sub(r"\s+", " ", answer).strip().strip('"').strip()

    low = answer.lower()
    if not answer or any(bad in low for bad in FORBIDDEN) or _looks_repetitive(answer):
        logging.warning("Rejected LLM answer: %r", answer[:220])
        return _local_reply(user_text) or random.choice(FALLBACKS)

    sentences = re.findall(r"[^.!?]{2,170}[.!?]", answer)
    if "joke" in user_text.lower() and len(sentences) >= 2:
        return " ".join(s.strip() for s in sentences[:2])
    if sentences:
        return sentences[0].strip()

    return answer[:220].strip()


def ask_llm(user_text: str, history: Iterable[dict] | None = None) -> str:
    local = _local_reply(user_text)
    if local:
        logging.info("Local answer: %r", local)
        return local

    endpoint = config.LLM_ENDPOINT.replace("/api/chat", "/api/generate")

    prompt = (
        "You are pi_friend, a small warm robot companion.\n"
        "You speak directly as pi_friend.\n"
        "Never say you are an AI, a language model, or a machine learning model.\n"
        "Do not pretend to be the user or copy the user's feelings as your own.\n"
        "Be kind, concrete, and natural.\n"
        "Answer in one short helpful sentence, or two short sentences if needed.\n"
        "Do not repeat words.\n"
        f"User: {user_text.strip()}\n"
        "pi_friend:"
    )

    payload = {
        "model": config.LLM_MODEL,
        "stream": False,
        "prompt": prompt,
        "options": {
            "num_predict": 52,
            "temperature": 0.35,
            "top_p": 0.9
        },
    }

    try:
        response = requests.post(endpoint, json=payload, timeout=config.LLM_TIMEOUT_SECONDS)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        logging.warning("LLM request failed: %s", exc)
        return random.choice(FALLBACKS)

    raw = ""
    if isinstance(data, dict):
        raw = data.get("response") or data.get("message", {}).get("content") or ""

    answer = _clean_answer(raw, user_text)
    logging.info("LLM answer: %r", answer)
    return answer
