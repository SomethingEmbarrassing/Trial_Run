# main.py
"""CLI interface for a Raspberry Pi chatbot with optional voice support.

The initial version only accepted typed input. This update introduces
continuous listening using the :mod:`speech_recognition` library and an
optional wake word. Audio input/output can be replaced with more advanced
libraries later.
"""

from typing import Optional, List, Tuple
import argparse

try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover - speech_recognition may not be installed
    sr = None


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


def send_to_openai(prompt: str, history: List[Tuple[str, str]]) -> str:
    """Placeholder for sending a prompt to the OpenAI API with context.

    Args:
        prompt: The user's question or statement.
        history: List of (speaker, text) tuples containing previous
            conversation turns.

    Returns a mock response string. Replace the body of this function with
    actual API calls once the `openai` package is installed and configured.
    """
    # TODO: integrate openai.Completion or Chat API
    print("[DEBUG] Sending to OpenAI:", prompt)
    print("[DEBUG] Conversation history:", history)
    return "This is a placeholder response from OpenAI."


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

    conversation_history: List[Tuple[str, str]] = []

    print("Press Ctrl+C to exit.")
    try:
        while True:
            if args.wake_word:
                listen_for_wake_word(
                    recognizer, args.wake_word, typed_input=args.use_typing
                )

            user_text = capture_audio(recognizer, typed_input=args.use_typing)
            if not user_text:
                continue
            conversation_history.append(("user", user_text))
            response = send_to_openai(user_text, conversation_history)
            conversation_history.append(("assistant", response))
            speak_text(response)
    except KeyboardInterrupt:
        print("\nExiting.")


if __name__ == "__main__":
    main()
