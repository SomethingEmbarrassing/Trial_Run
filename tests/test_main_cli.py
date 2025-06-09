import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import sys
from unittest import mock

import main


def test_cli_options(monkeypatch):
    events = {}

    def fake_capture_audio(recognizer, *, typed_input=False):
        events['typed_input'] = typed_input
        if 'called' in events:
            raise KeyboardInterrupt
        events['called'] = True
        return 'hello'

    def fake_send_to_openai(prompt):
        events['prompt'] = prompt
        return 'hi'

    def fake_speak_text(text, *, tts_enabled=True, engine='pyttsx3'):
        events['tts_enabled'] = tts_enabled
        events['engine'] = engine

    def fake_listen_for_wake_word(recognizer, wake_word, *, typed_input=False):
        events['wake_word'] = wake_word

    monkeypatch.setattr(main, 'capture_audio', fake_capture_audio)
    monkeypatch.setattr(main, 'send_to_openai', fake_send_to_openai)
    monkeypatch.setattr(main, 'speak_text', fake_speak_text)
    monkeypatch.setattr(main, 'listen_for_wake_word', fake_listen_for_wake_word)
    monkeypatch.setattr(main, 'sr', None)

    argv = ['prog', '--use-typing', '--no-tts', '--tts-engine', 'gtts', '--wake-word', 'yo']
    monkeypatch.setattr(sys, 'argv', argv)

    main.main()

    assert events['typed_input'] is True
    assert events['tts_enabled'] is False
    assert events['engine'] == 'gtts'
    assert events['wake_word'] == 'yo'
    assert events['prompt'] == 'hello'
