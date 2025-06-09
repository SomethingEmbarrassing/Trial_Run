# Trial_Run

## Project Overview
This repository contains the initial work for a Raspberry Pi–based voice chatbot. The goal is to embed a Pi 4 inside a plastic skull with a microphone and speaker so it can converse using OpenAI and sound like Bob the skull from *The Dresden Files*. Responses will be generated using the OpenAI API and read aloud via a text-to-speech engine.

## Getting Started
1. **Install Python 3** (if not already present)
   ```bash
   sudo apt-get update
   sudo apt-get install python3 python3-pip
   ```
2. **Install required libraries**
   ```bash
   pip install -r requirements.txt
   ```
   The `requirements.txt` file lists the core packages (`speechrecognition`,
   `pyttsx3` and `openai`) and notes the optional `RPi.GPIO` dependency for
   Raspberry Pi hardware. You can substitute another text-to-speech engine if
   preferred.
3. **Configure your OpenAI API key**
   ```bash
   export OPENAI_API_KEY=<your-api-key>
   ```
   Add this line to your shell profile (e.g., `.bashrc`) so the application can access the key at runtime.

## Roadmap / Next Steps
- Maintain conversation history for context
- Hardware controls for microphone and speaker

### New Features
- **Continuous listening mode**: the chatbot can now listen for speech input
  in a loop. Run with microphone support (requires the ``speechrecognition``
  package) or use ``--use-typing`` to fall back to keyboard input.
- **Optional wake word**: supply ``--wake-word <word>`` to require a wake word
  before the assistant records the next prompt.
- **Text-to-speech options**: choose ``--tts-engine pyttsx3`` or ``gtts`` and
  pass ``--no-tts`` to disable audio output entirely.

## Usage

Run the chatbot with the microphone and offline text-to-speech (``pyttsx3``) like so:
```bash
python3 main.py
```

If you prefer to type your prompts, add ``--use-typing``. To require a wake word
before each prompt, supply ``--wake-word <word>``. You can switch to Google TTS
with ``--tts-engine gtts`` or disable audio entirely using ``--no-tts``.

The script sends each prompt to OpenAI using the ``OPENAI_API_KEY`` environment
variable. Responses are spoken aloud with the chosen TTS engine and printed to
the console.
