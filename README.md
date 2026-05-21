# Trial_Run

## Project Overview
This repository contains a Raspberry Pi–based voice chatbot prototype. The long-term goal is to run it inside a prop skull with a microphone, speaker, wake word activation, and OpenAI-backed conversation.

## Getting Started
1. Install Python and dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set your API key:
   ```bash
   export OPENAI_API_KEY=<your-api-key>
   ```
3. Run:
   ```bash
   python3 main.py --use-typing
   ```

## Current Features
- Continuous conversation loop
- Optional wake word (`--wake-word`)
- Typed input fallback (`--use-typing`)
- TTS via `pyttsx3` or `gtts` (`--tts-engine`)
- Optional history persistence (`--history-file`)
- Optional GPIO mic/speaker control (`--mic-pin`, `--speaker-pin`)

## Refreshed Roadmap (2026)

### Phase 1: Stabilize the Core (next)
- Add structured configuration (env + config file + CLI precedence)
- Add robust logging (info/debug/error) and better runtime diagnostics
- Add history limits/summarization to prevent token bloat
- Expand tests around persistence and error paths

### Phase 2: Modernize OpenAI Integration
- Add a dedicated OpenAI client module
- Support model configuration by CLI/env
- Add retry/backoff for transient API failures
- Add optional streaming responses for lower perceived latency

### Phase 3: Hardware Reliability
- Improve GPIO abstraction to support non-RPi dev environments cleanly
- Add push-to-talk mode and audio device selection
- Add graceful recovery for microphone/speaker initialization failures

### Phase 4: Product Experience
- Persona prompt management (e.g., “Bob voice profile” presets)
- Session commands (clear history, save snapshot, status)
- Packaging for Raspberry Pi deployment (systemd service + install script)

## Running Tests
```bash
pytest -q
```
