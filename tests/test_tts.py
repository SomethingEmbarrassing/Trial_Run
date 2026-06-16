import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest import mock
import tts


def test_speak_no_tts_skips_engine(capsys):
    """speak_text with tts_enabled=False should just print, not call any engine."""
    with mock.patch.object(tts, "_speak_pyttsx3") as mock_p:
        # Call the main module speak_text wrapper
        import main
        main.speak_text("hello", tts_enabled=False)
        mock_p.assert_not_called()
    out = capsys.readouterr().out
    assert "hello" in out


def test_speak_routes_to_pyttsx3(monkeypatch):
    called = {}
    monkeypatch.setattr(tts, "_speak_pyttsx3", lambda text: called.update({"text": text}))
    tts.speak("hi", engine="pyttsx3")
    assert called["text"] == "hi"


def test_speak_routes_to_gtts(monkeypatch):
    called = {}
    monkeypatch.setattr(tts, "_speak_gtts", lambda text: called.update({"text": text}))
    tts.speak("hello", engine="gtts")
    assert called["text"] == "hello"


def test_speak_routes_to_local_rvc(monkeypatch):
    called = {}
    monkeypatch.setattr(
        tts, "_speak_local_rvc",
        lambda text, server_url="": called.update({"text": text, "url": server_url}),
    )
    tts.speak("hello", engine="local-rvc", server_url="http://mypc:5050")
    assert called["text"] == "hello"
    assert called["url"] == "http://mypc:5050"


def test_speak_routes_to_elevenlabs(monkeypatch):
    called = {}
    monkeypatch.setattr(
        tts, "_speak_elevenlabs", lambda text, voice_id="": called.update({"text": text, "vid": voice_id})
    )
    tts.speak("test", engine="elevenlabs", voice_id="abc123")
    assert called["text"] == "test"
    assert called["vid"] == "abc123"


def test_elevenlabs_missing_voice_id(capsys):
    tts._speak_elevenlabs("hi", voice_id="")
    assert "voice-id" in capsys.readouterr().out


def test_elevenlabs_missing_api_key(monkeypatch, capsys):
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    tts._speak_elevenlabs("hi", voice_id="some-id")
    assert "ELEVENLABS_API_KEY" in capsys.readouterr().out


def test_elevenlabs_missing_package(monkeypatch, capsys):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "fake-key")
    monkeypatch.setattr(tts, "_optional", lambda name: None)
    tts._speak_elevenlabs("hi", voice_id="some-id")
    assert "elevenlabs" in capsys.readouterr().out.lower()


def test_elevenlabs_calls_api(monkeypatch, tmp_path):
    monkeypatch.setenv("ELEVENLABS_API_KEY", "fake-key")

    fake_audio = [b"chunk1", b"chunk2"]
    mock_client = mock.MagicMock()
    mock_client.text_to_speech.convert.return_value = iter(fake_audio)

    mock_el = mock.MagicMock()
    mock_el.ElevenLabs.return_value = mock_client
    monkeypatch.setattr(tts, "_optional", lambda name: mock_el if name == "elevenlabs" else None)

    played = {}

    def fake_play(path):
        played["path"] = path
        # verify file exists with expected content
        with open(path, "rb") as f:
            played["bytes"] = f.read()

    monkeypatch.setattr(tts, "_play_audio_file", fake_play)

    tts._speak_elevenlabs("hello Bob", voice_id="vid-123")

    mock_client.text_to_speech.convert.assert_called_once_with(
        voice_id="vid-123",
        text="hello Bob",
        model_id="eleven_turbo_v2_5",
        output_format="mp3_44100_128",
    )
    assert played["bytes"] == b"chunk1chunk2"


def test_local_rvc_missing_requests(monkeypatch, capsys):
    monkeypatch.setattr(tts, "_optional", lambda name: None)
    tts._speak_local_rvc("hi", server_url="http://localhost:5050")
    assert "requests" in capsys.readouterr().out


def test_local_rvc_server_error(monkeypatch, capsys):
    mock_requests = mock.MagicMock()
    mock_requests.post.side_effect = ConnectionError("refused")
    monkeypatch.setattr(tts, "_optional", lambda name: mock_requests if name == "requests" else None)
    tts._speak_local_rvc("hi", server_url="http://localhost:5050")
    assert "unreachable" in capsys.readouterr().out


def test_local_rvc_plays_wav(monkeypatch):
    fake_audio = b"RIFF....WAVEfmt "
    mock_response = mock.MagicMock()
    mock_response.raise_for_status.return_value = None
    mock_response.content = fake_audio

    mock_requests = mock.MagicMock()
    mock_requests.post.return_value = mock_response
    monkeypatch.setattr(tts, "_optional", lambda name: mock_requests if name == "requests" else None)

    played = {}
    monkeypatch.setattr(tts, "_play_audio_file", lambda path: played.update({"path": path}))

    tts._speak_local_rvc("You rang, Harry?", server_url="http://mypc:5050")

    mock_requests.post.assert_called_once_with(
        "http://mypc:5050/synthesize",
        json={"text": "You rang, Harry?"},
        timeout=30,
    )
    assert played["path"].endswith(".wav")


def test_speak_hardware_ctrl_called(monkeypatch):
    monkeypatch.setattr(tts, "_speak_pyttsx3", lambda text: None)
    hw = mock.MagicMock()
    tts.speak("test", engine="pyttsx3", hardware_ctrl=hw)
    hw.speaker_on.assert_called_once()
    hw.speaker_off.assert_called_once()


def test_speak_hardware_ctrl_off_on_error(monkeypatch):
    def boom(text):
        raise RuntimeError("tts exploded")

    monkeypatch.setattr(tts, "_speak_pyttsx3", boom)
    hw = mock.MagicMock()
    tts.speak("test", engine="pyttsx3", hardware_ctrl=hw)
    hw.speaker_on.assert_called_once()
    hw.speaker_off.assert_called_once()
