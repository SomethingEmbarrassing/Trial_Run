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
    import RPi.GPIO as GPIO  # pragma: no cover - may not be installed
except ImportError:  # pragma: no cover - GPIO library might not be available
    GPIO = None

try:
    import speech_recognition as sr
except ImportError:  # pragma: no cover - speech_recognition may not be installed
    sr = None


class HardwareController:
    """Control GPIO pins for microphone and speaker power."""

    def __init__(self, mic_pin: Optional[int] = None, speaker_pin: Optional[int] = None) -> None:
        self.mic_pin = mic_pin
        self.speaker_pin = speaker_pin
        self.gpio = GPIO
        if self.gpio and (mic_pin is not None or speaker_pin is not None):
            self.gpio.setmode(self.gpio.BCM)
            if mic_pin is not None:
                self.gpio.setup(mic_pin, self.gpio.OUT, initial=self.gpio.HIGH)
            if speaker_pin is not None:
                self.gpio.setup(speaker_pin, self.gpio.OUT, initial=self.gpio.HIGH)
        elif mic_pin is not None or speaker_pin is not None:
            print("[DEBUG] RPi.GPIO not available; hardware control disabled")

    def mic_on(self) -> None:
        if self.gpio and self.mic_pin is not None:
            self.gpio.output(self.mic_pin, self.gpio.HIGH)
        print("[DEBUG] Mic ON")

    def mic_off(self) -> None:
        if self.gpio and self.mic_pin is not None:
            self.gpio.output(self.mic_pin, self.gpio.LOW)
        print("[DEBUG] Mic OFF")

    def speaker_on(self) -> None:
        if self.gpio and self.speaker_pin is not None:
            self.gpio.output(self.speaker_pin, self.gpio.HIGH)
        print("[DEBUG] Speaker ON")

    def speaker_off(self) -> None:
        if self.gpio and self.speaker_pin is not None:
            self.gpio.output(self.speaker_pin, self.gpio.LOW)
        print("[DEBUG] Speaker OFF")

    def cleanup(self) -> None:
        if self.gpio and (self.mic_pin is not None or self.speaker_pin is not None):
            self.gpio.cleanup()


def capture_audio(
    recognizer: Optional["sr.Recognizer"] = None,
    *,
    typed_input: bool = False,
    hardware: Optional["HardwareController"] = None,
) -> str:
    """Capture a single utterance from the user.

    If ``typed_input`` is True or no microphone support is available, this
    falls back to ``input()``. Otherwise it listens on the microphone using
    ``speech_recognition``.
    """
    if typed_input or recognizer is None or sr is None:
        if hardware:
            hardware.mic_on()
        text = input("You: ")
        if hardware:
            hardware.mic_off()
        return text

    with sr.Microphone() as source:
        if hardware:
            hardware.mic_on()
        print("Listening...")
        audio = recognizer.listen(source)
        if hardware:
            hardware.mic_off()

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


def listen_for_wake_word(
    recognizer: Optional["sr.Recognizer"],
    wake_word: str,
    *,
    typed_input: bool = False,
    hardware: Optional["HardwareController"] = None,
) -> None:
    """Block until the wake word is detected."""
    if not wake_word:
        return
    prompt = f"Say or type '{wake_word}' to activate."
    print(prompt)
    while True:
        text = capture_audio(recognizer, typed_input=typed_input, hardware=hardware)
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


def speak_text(text: str, *, hardware: Optional["HardwareController"] = None) -> None:
    """Placeholder for text-to-speech output.

    Args:
        text: The response text to vocalize.

    Currently prints the text to the console. Replace with a TTS library
    (e.g., pyttsx3 or gTTS) to output audio.
    """
    if hardware:
        hardware.speaker_on()
    print("Bot:", text)
    if hardware:
        hardware.speaker_off()


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
    parser.add_argument(
        "--mic-pin",
        type=int,
        help="GPIO pin used to power the microphone",
    )
    parser.add_argument(
        "--speaker-pin",
        type=int,
        help="GPIO pin used to power the speaker",
    )
    args = parser.parse_args()

    recognizer = sr.Recognizer() if sr and not args.use_typing else None

    hardware = HardwareController(args.mic_pin, args.speaker_pin)

    conversation_history: List[Tuple[str, str]] = []

    print("Press Ctrl+C to exit.")
    try:
        while True:
            if args.wake_word:
                listen_for_wake_word(
                    recognizer,
                    args.wake_word,
                    typed_input=args.use_typing,
                    hardware=hardware,
                )

            user_text = capture_audio(
                recognizer, typed_input=args.use_typing, hardware=hardware
            )
            if not user_text:
                continue
            conversation_history.append(("user", user_text))
            response = send_to_openai(user_text, conversation_history)
            conversation_history.append(("assistant", response))
            speak_text(response, hardware=hardware)
    except KeyboardInterrupt:
        print("\nExiting.")
    finally:
        hardware.cleanup()


if __name__ == "__main__":
    main()
