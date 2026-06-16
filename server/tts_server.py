"""
Bob skull TTS server — runs on the always-on local PC.
Pipeline: text → Piper (base voice) → RVC (James Marsters conversion) → WAV audio

Start with:
    python server/tts_server.py \
        --piper-model /path/to/en_US-lessac-medium.onnx \
        --rvc-model   /path/to/james_marsters.pth \
        --rvc-index   /path/to/james_marsters.index
"""

from __future__ import annotations

import argparse
import os
import subprocess
import tempfile

from flask import Flask, Response, jsonify, request

app = Flask(__name__)

# Loaded once at startup — kept alive across requests to avoid model reload overhead
_rvc_instance = None


@app.post("/synthesize")
def synthesize() -> tuple | Response:
    text = (request.get_json(silent=True) or {}).get("text", "").strip()
    if not text:
        return jsonify(error="text is required"), 400

    piper_wav = tempfile.mktemp(suffix=".wav")
    rvc_wav = tempfile.mktemp(suffix=".wav")
    try:
        _piper_synthesize(text, piper_wav)
        _rvc_convert(piper_wav, rvc_wav)
        with open(rvc_wav, "rb") as f:
            audio = f.read()
        return Response(audio, mimetype="audio/wav")
    except RuntimeError as exc:
        return jsonify(error=str(exc)), 500
    finally:
        for path in (piper_wav, rvc_wav):
            try:
                os.remove(path)
            except FileNotFoundError:
                pass


def _piper_synthesize(text: str, output_path: str) -> None:
    result = subprocess.run(
        ["piper", "--model", app.config["PIPER_MODEL"], "--output_file", output_path],
        input=text.encode(),
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Piper failed: {result.stderr.decode().strip()}")


def _rvc_convert(input_path: str, output_path: str) -> None:
    if _rvc_instance is None:
        raise RuntimeError("RVC model not loaded — was load_rvc() called at startup?")
    _rvc_instance.infer(input_path, output_path)


def load_rvc(model_path: str, index_path: str = "") -> None:
    global _rvc_instance
    try:
        from rvc_python.infer import RVCInference
    except ImportError:
        raise SystemExit("[ERROR] rvc-python not installed — run: pip install rvc-python")
    rvc = RVCInference()
    rvc.load_model(model_path, index_path)
    _rvc_instance = rvc
    print(f"[INFO] RVC model loaded: {model_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Bob skull local TTS server")
    parser.add_argument("--piper-model", required=True, help="Path to Piper .onnx voice model")
    parser.add_argument("--rvc-model", required=True, help="Path to RVC .pth model file")
    parser.add_argument(
        "--rvc-index", default="", help="Path to RVC .index file (optional but improves accuracy)"
    )
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5050)
    args = parser.parse_args()

    app.config["PIPER_MODEL"] = args.piper_model
    load_rvc(args.rvc_model, args.rvc_index)

    print(f"[INFO] TTS server listening on {args.host}:{args.port}")
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
