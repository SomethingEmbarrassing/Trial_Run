import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest import mock
import pytest

import server.tts_server as srv


@pytest.fixture(autouse=True)
def reset_rvc():
    """Ensure RVC singleton is cleared between tests."""
    srv._rvc_instance = None
    srv.app.config["PIPER_MODEL"] = "fake.onnx"
    yield
    srv._rvc_instance = None


@pytest.fixture()
def client():
    srv.app.config["TESTING"] = True
    with srv.app.test_client() as c:
        yield c


def test_synthesize_missing_text(client):
    resp = client.post("/synthesize", json={})
    assert resp.status_code == 400
    assert b"text" in resp.data


def test_synthesize_empty_text(client):
    resp = client.post("/synthesize", json={"text": "   "})
    assert resp.status_code == 400


def test_synthesize_no_json(client):
    resp = client.post("/synthesize", data="not json", content_type="text/plain")
    assert resp.status_code == 400


def test_synthesize_piper_failure(client):
    mock_rvc = mock.MagicMock()
    srv._rvc_instance = mock_rvc

    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=1, stderr=b"model not found")
        resp = client.post("/synthesize", json={"text": "hello Bob"})

    assert resp.status_code == 500
    assert b"Piper" in resp.data


def test_synthesize_rvc_not_loaded(client):
    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0)
        resp = client.post("/synthesize", json={"text": "hello"})
    assert resp.status_code == 500
    assert b"RVC" in resp.data


def test_synthesize_happy_path(client, tmp_path):
    fake_wav = b"RIFF....WAVEfmt "
    mock_rvc = mock.MagicMock()

    def fake_infer(input_path, output_path):
        with open(output_path, "wb") as f:
            f.write(fake_wav)

    mock_rvc.infer.side_effect = fake_infer
    srv._rvc_instance = mock_rvc

    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0)
        resp = client.post("/synthesize", json={"text": "You rang, Harry?"})

    assert resp.status_code == 200
    assert resp.mimetype == "audio/wav"
    assert resp.data == fake_wav
    mock_rvc.infer.assert_called_once()


def test_piper_command_uses_configured_model(client):
    mock_rvc = mock.MagicMock()
    srv._rvc_instance = mock_rvc
    srv.app.config["PIPER_MODEL"] = "/models/en_US-lessac-medium.onnx"

    def fake_infer(inp, out):
        with open(out, "wb") as f:
            f.write(b"audio")

    mock_rvc.infer.side_effect = fake_infer

    with mock.patch("subprocess.run") as mock_run:
        mock_run.return_value = mock.Mock(returncode=0)
        client.post("/synthesize", json={"text": "test"})

    cmd = mock_run.call_args[0][0]
    assert "/models/en_US-lessac-medium.onnx" in cmd
    assert "piper" in cmd


def test_load_rvc_missing_package():
    with mock.patch.dict("sys.modules", {"rvc_python": None, "rvc_python.infer": None}):
        with pytest.raises(SystemExit, match="rvc-python"):
            srv.load_rvc("model.pth")


def test_load_rvc_success():
    mock_rvc_cls = mock.MagicMock()
    mock_instance = mock.MagicMock()
    mock_rvc_cls.return_value = mock_instance

    mock_module = mock.MagicMock()
    mock_module.RVCInference = mock_rvc_cls

    with mock.patch.dict("sys.modules", {"rvc_python": mock_module, "rvc_python.infer": mock_module}):
        srv.load_rvc("model.pth", "model.index")

    mock_instance.load_model.assert_called_once_with("model.pth", "model.index")
    assert srv._rvc_instance is mock_instance
