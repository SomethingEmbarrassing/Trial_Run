"""Text-to-speech engine abstraction."""

from __future__ import annotations

import importlib
import os
import tempfile
from typing import Any


def _optional(name: str) -> Any:
    try:
        return importlib.import_module(name)
    except Exception:
        return None


def speak(
    text: str,
    *,
    engine: str = "pyttsx3",
    voice_id: str = "",
    hardware_ctrl=None,
) -> None:
    print("Bot:", text)

    if hardware_ctrl is not None:
        hardware_ctrl.speaker_on()
    try:
        if engine == "elevenlabs":
            _speak_elevenlabs(text, voice_id=voice_id)
        elif engine == "gtts":
            _speak_gtts(text)
        else:
            _speak_pyttsx3(text)
    except Exception as exc:
        print(f"[ERROR] TTS error: {exc}")
    finally:
        if hardware_ctrl is not None:
            hardware_ctrl.speaker_off()


def _speak_pyttsx3(text: str) -> None:
    pyttsx3 = _optional("pyttsx3")
    if pyttsx3 is None:
        print("[WARN] pyttsx3 not installed")
        return
    eng = pyttsx3.init()
    eng.say(text)
    eng.runAndWait()


def _speak_gtts(text: str) -> None:
    gtts_module = _optional("gtts")
    playsound_module = _optional("playsound")
    if gtts_module is None or playsound_module is None:
        print("[WARN] gTTS or playsound not installed")
        return
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        gtts_module.gTTS(text=text).save(fp.name)
        fname = fp.name
    playsound_module.playsound(fname)
    os.remove(fname)


def _speak_elevenlabs(text: str, *, voice_id: str = "") -> None:
    if not voice_id:
        print("[ERROR] --voice-id is required for ElevenLabs TTS")
        return

    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        print("[ERROR] ELEVENLABS_API_KEY environment variable not set")
        return

    elevenlabs = _optional("elevenlabs")
    if elevenlabs is None:
        print("[WARN] elevenlabs package not installed — run: pip install elevenlabs")
        return

    client = elevenlabs.ElevenLabs(api_key=api_key)
    audio_chunks = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        # eleven_turbo_v2_5 gives the lowest latency — good for Pi real-time use
        model_id="eleven_turbo_v2_5",
        output_format="mp3_44100_128",
    )
    audio_bytes = b"".join(audio_chunks)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        fp.write(audio_bytes)
        fname = fp.name

    try:
        _play_audio_file(fname)
    finally:
        os.remove(fname)


def _play_audio_file(path: str) -> None:
    """Play an audio file using pygame (preferred on Pi) or playsound."""
    pygame = _optional("pygame")
    if pygame is not None:
        pygame.mixer.init()
        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.quit()
        return

    playsound = _optional("playsound")
    if playsound is not None:
        playsound.playsound(path)
        return

    print("[WARN] No audio playback library available — install pygame or playsound")
