# main.py
"""Simple CLI interface for a Raspberry Pi chatbot.

This file defines placeholder functions for capturing audio, sending text to
OpenAI's API, and generating speech. The current implementation uses standard
input/output so you can test the conversation loop without additional
libraries. Audio input/output libraries can be added later.
"""

from typing import Optional


def capture_audio() -> str:
    """Placeholder for microphone input.

    Returns text typed by the user for now.
    """
    return input("You: ")


def send_to_openai(prompt: str) -> str:
    """Placeholder for sending a prompt to the OpenAI API.

    Args:
        prompt: The user's question or statement.

    Returns a mock response string. Replace the body of this function with
    actual API calls once the `openai` package is installed and configured.
    """
    # TODO: integrate openai.Completion or Chat API
    print("[DEBUG] Sending to OpenAI:", prompt)
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
    """Run a single-turn conversation loop."""
    print("Press Ctrl+C to exit.")
    try:
        while True:
            user_text = capture_audio()
            if not user_text:
                continue
            response = send_to_openai(user_text)
            speak_text(response)
    except KeyboardInterrupt:
        print("\nExiting.")


if __name__ == "__main__":
    main()
