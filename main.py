# main.py
"""CLI interface for a Raspberry Pi chatbot with optional voice support.

The initial version only accepted typed input. This update introduces
continuous listening using the :mod:`speech_recognition` library and an
optional wake word. Audio input/output can be replaced with more advanced
libraries later.
"""

from typing import Optional
import argparse
import os

try:
    import openai
    from openai.error import OpenAIError
except ImportError:  # pragma: no cover - openai may not be installed
    openai = None  # type: ignore
    OpenAIError = Exception  # type: ignore

try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover - speech_recognition may not be installed
    sr = None

# Configure OpenAI API if available
if openai is not None:
    openai.api_key = os.getenv("OPENAI_API_KEY")

# Conversation history for chat context
history = [
    {
        "role": "system",
        "content": "You are a helpful assistant."
    }
]


def capture_audio(recognizer: Optional["sr.Recognizer"] = None, *, typed_input: bool = False) -> str:
    """Capture a single utterance from the user.

    If ``typed_input`` is True or no microphone support is available, this
    falls back to ``input()``. Otherwise it listens on the microphone using
    ``speech_recognition``.
    """
    if typed_input or recognizer is None or sr is None:
        return input("You: ")

    with sr.Microphone() as source:
        print("Listening...")
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print(f"You said: {text}")
        return text
    except sr.UnknownValueError:
        print("[DEBUG] Could not understand audio")
        return ""
    except sr.RequestError as exc:
        print(f"[DEBUG] Speech recognition error: {exc}")
        return ""


def listen_for_wake_word(recognizer: Optional["sr.Recognizer"], wake_word: str, *, typed_input: bool = False) -> None:
    """Block until the wake word is detected."""
    if not wake_word:
        return
    prompt = f"Say or type '{wake_word}' to activate."
    print(prompt)
    while True:
        text = capture_audio(recognizer, typed_input=typed_input)
        if wake_word.lower() in text.lower():
            return


def send_to_openai(prompt: str) -> str:
    """Send ``prompt`` to the OpenAI Chat API using ``history`` for context."""

    if openai is None:
        print("[ERROR] The openai package is not installed.")
        return "OpenAI support is unavailable."

    if not openai.api_key:
        print("[ERROR] OPENAI_API_KEY environment variable not set.")
        return "OpenAI API key missing."

    history.append({"role": "user", "content": prompt})
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=history,
        )
        text = response.choices[0].message["content"].strip()
        history.append({"role": "assistant", "content": text})
        return text
    except OpenAIError as exc:
        print(f"[ERROR] OpenAI API error: {exc}")
        return "Sorry, I couldn't reach OpenAI."
    except Exception as exc:  # pragma: no cover - unexpected errors
        print(f"[ERROR] Unexpected error: {exc}")
        return "Sorry, something went wrong."


def speak_text(text: str) -> None:
    """Placeholder for text-to-speech output.

    Args:
        text: The response text to vocalize.

    Currently prints the text to the console. Replace with a TTS library
    (e.g., pyttsx3 or gTTS) to output audio.
    """
    print("Bot:", text)


def main() -> None:
    """Run the conversation loop."""
    parser = argparse.ArgumentParser(description="Simple voice chatbot demo")
    parser.add_argument(
        "--wake-word",
        help="Optional wake word required before capturing speech",
    )
    parser.add_argument(
        "--use-typing",
        action="store_true",
        help="Use typed input instead of microphone audio",
    )
    args = parser.parse_args()

    recognizer = sr.Recognizer() if sr and not args.use_typing else None

    print("Press Ctrl+C to exit.")
    try:
        while True:
            if args.wake_word:
                listen_for_wake_word(recognizer, args.wake_word, typed_input=args.use_typing)

            user_text = capture_audio(recognizer, typed_input=args.use_typing)
            if not user_text:
                continue
            response = send_to_openai(user_text)
            speak_text(response)
    except KeyboardInterrupt:
        print("\nExiting.")


if __name__ == "__main__":
    main()
