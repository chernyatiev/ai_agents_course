"""Вызов LLM через OpenAI-совместимый API (OpenRouter, Ollama, ...).

Никаких SDK: один POST-запрос на /chat/completions.
"""
import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1").rstrip("/")
API_KEY = os.getenv("LLM_API_KEY", "")
MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")


def chat(messages: list[dict], tools: list[dict]) -> dict:
    """Отправляет историю и описания инструментов, возвращает сообщение ассистента."""
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    if os.getenv("SHOW_TOOLS"):  # демо: что именно модель знает об инструментах
        print(json.dumps(tools, ensure_ascii=False, indent=2))

    response = requests.post(
        f"{BASE_URL}/chat/completions",
        headers=headers,
        json={"model": MODEL, "messages": messages, "tools": tools},
        timeout=120,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]
