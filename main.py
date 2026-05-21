"""CLI interface for a Raspberry Pi chatbot with optional voice support."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import tempfile
from typing import Any, Optional

from hardware import HardwareController


def optional_import(module_name: str) -> Any:
    """Import ``module_name`` and return ``None`` if unavailable."""
    try:
        return importlib.import_module(module_name)
    except Exception:  # pragma: no cover - optional dependency
        return None


pyttsx3 = optional_import("pyttsx3")
gtts_module = optional_import("gtts")
playsound_module = optional_import("playsound")
openai = optional_import("openai")
sr = optional_import("speech_recognition")

if openai is not None and hasattr(openai, "api_key"):
    openai.api_key = os.getenv("OPENAI_API_KEY")

history = [{"role": "system", "content": "You are a helpful assistant."}]


def load_history(path: str) -> None:
    if not path or not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            history.extend(item for item in data if isinstance(item, dict))
    except Exception as exc:  # pragma: no cover
        print(f"[WARN] Could not load history file: {exc}")


def save_history(path: str) -> None:
    if not path:
        return
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(history[1:], f, indent=2)
    except Exception as exc:  # pragma: no cover
        print(f"[WARN] Could not save history file: {exc}")


def capture_audio(recognizer=None, *, typed_input: bool = False, hardware_ctrl=None) -> str:
    if typed_input or recognizer is None or sr is None:
        return input("You: ")

    if hardware_ctrl is not None:
        hardware_ctrl.mic_on()
    try:
        with sr.Microphone() as source:
            print("Listening...")
            audio = recognizer.listen(source)
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("[DEBUG] Could not understand audio")
        return ""
    except sr.RequestError as exc:
        print(f"[DEBUG] Speech recognition error: {exc}")
        return ""
    finally:
        if hardware_ctrl is not None:
            hardware_ctrl.mic_off()


def listen_for_wake_word(recognizer, wake_word: str, *, typed_input: bool = False, hardware_ctrl=None) -> None:
    if not wake_word:
        return
    print(f"Say or type '{wake_word}' to activate.")
    while True:
        text = capture_audio(recognizer, typed_input=typed_input, hardware_ctrl=hardware_ctrl)
        if wake_word.lower() in text.lower():
            return


def _send_with_legacy_openai(prompt: str) -> str:
    history.append({"role": "user", "content": prompt})
    response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=history)
    text = response.choices[0].message["content"].strip()
    history.append({"role": "assistant", "content": text})
    return text


def send_to_openai(prompt: str) -> str:
    if openai is None:
        print("[ERROR] The openai package is not installed.")
        return "OpenAI support is unavailable."

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("[ERROR] OPENAI_API_KEY environment variable not set.")
        return "OpenAI API key missing."

    try:
        if hasattr(openai, "OpenAI"):
            client = openai.OpenAI(api_key=api_key)
            history.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model="gpt-4o-mini", messages=history)
            text = (response.choices[0].message.content or "").strip()
            history.append({"role": "assistant", "content": text})
            return text
        return _send_with_legacy_openai(prompt)
    except Exception as exc:  # pragma: no cover
        print(f"[ERROR] OpenAI API error: {exc}")
        return "Sorry, I couldn't reach OpenAI."


def speak_text(text: str, *, tts_enabled: bool = True, engine: str = "pyttsx3", hardware_ctrl=None) -> None:
    print("Bot:", text)
    if not tts_enabled:
        return

    if hardware_ctrl is not None:
        hardware_ctrl.speaker_on()

    try:
        if engine == "pyttsx3":
            if pyttsx3 is None:
                print("[WARN] pyttsx3 not installed")
                return
            tts_engine = pyttsx3.init()
            tts_engine.say(text)
            tts_engine.runAndWait()
        else:
            if gtts_module is None or playsound_module is None:
                print("[WARN] gTTS or playsound not installed")
                return
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                gtts_module.gTTS(text=text).save(fp.name)
            playsound_module.playsound(fp.name)
            os.remove(fp.name)
    except Exception as exc:  # pragma: no cover
        print(f"[ERROR] TTS error: {exc}")
    finally:
        if hardware_ctrl is not None:
            hardware_ctrl.speaker_off()


def main() -> None:
    parser = argparse.ArgumentParser(description="Simple voice chatbot demo")
    parser.add_argument("--wake-word")
    parser.add_argument("--use-typing", action="store_true")
    parser.add_argument("--tts-engine", choices=["pyttsx3", "gtts"], default="pyttsx3")
    parser.add_argument("--no-tts", action="store_true")
    parser.add_argument("--history-file")
    parser.add_argument("--mic-pin", type=int)
    parser.add_argument("--speaker-pin", type=int)
    args = parser.parse_args()

    recognizer = sr.Recognizer() if sr and not args.use_typing else None
    tts_enabled = not args.no_tts

    hardware_ctrl = None
    if args.mic_pin is not None and args.speaker_pin is not None:
        try:
            hardware_ctrl = HardwareController(args.mic_pin, args.speaker_pin)
        except Exception as exc:  # pragma: no cover
            print(f"[WARN] Could not initialize hardware controller: {exc}")

    if args.history_file:
        load_history(args.history_file)

    print("Press Ctrl+C to exit.")
    try:
        while True:
            if args.wake_word:
                listen_for_wake_word(recognizer, args.wake_word, typed_input=args.use_typing, hardware_ctrl=hardware_ctrl)
            user_text = capture_audio(recognizer, typed_input=args.use_typing, hardware_ctrl=hardware_ctrl)
            if not user_text:
                continue
            response = send_to_openai(user_text)
            speak_text(response, tts_enabled=tts_enabled, engine=args.tts_engine, hardware_ctrl=hardware_ctrl)
            if args.history_file:
                save_history(args.history_file)
    except KeyboardInterrupt:
        print("\nExiting.")
    finally:
        if hardware_ctrl is not None:
            hardware_ctrl.cleanup()


if __name__ == "__main__":
    main()
