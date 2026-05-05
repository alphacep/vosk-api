#!/usr/bin/env python3
"""
Twilio Elastic SIP Trunk — Incoming call handler with real-time Vosk transcription.

Setup in Twilio Console:
  Elastic SIP Trunks -> <your trunk> -> Voice Configuration
    -> Voice URL: https://<your-host>/incoming  (HTTP POST)

Audio pipeline per call:
  Twilio Media Stream (μ-law 8 kHz mono)
    -> ulaw2lin  -> PCM 16-bit 8 kHz
    -> ratecv   -> PCM 16-bit 16 kHz
    -> Vosk KaldiRecognizer
    -> logged transcripts (partial + final)

Environment variables:
  VOSK_MODEL_PATH   Path to a Vosk model directory (default: "model")
  PORT              HTTP/WS listen port              (default: 5000)
"""

import audioop
import base64
import json
import logging
import os

from flask import Flask, Response, request
from flask_sock import Sock
from vosk import KaldiRecognizer, Model, SetLogLevel

SetLogLevel(-1)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("twilio_vosk")

app = Flask(__name__)
sock = Sock(app)

# Twilio Media Streams always deliver μ-law at 8 000 Hz.
TWILIO_SAMPLE_RATE = 8_000
# Standard Vosk models are trained at 16 000 Hz.
VOSK_SAMPLE_RATE = 16_000

MODEL_PATH = os.getenv("VOSK_MODEL_PATH", "model")
_model: Model | None = None


def get_model() -> Model:
    global _model
    if _model is None:
        logger.info("Loading Vosk model from: %s", MODEL_PATH)
        _model = Model(MODEL_PATH)
        logger.info("Vosk model ready")
    return _model


# ---------------------------------------------------------------------------
# HTTP webhook — returns TwiML that opens a Media Stream back to this server
# ---------------------------------------------------------------------------

@app.route("/incoming", methods=["POST"])
def incoming_call() -> Response:
    """
    Twilio posts here when a call arrives on the Elastic SIP Trunk.
    We respond with TwiML that connects a bi-directional Media Stream so
    Twilio will forward raw audio to our WebSocket endpoint.
    """
    caller = request.form.get("From", "unknown")
    called = request.form.get("To", "unknown")
    call_sid = request.form.get("CallSid", "unknown")
    logger.info("Incoming call  sid=%s  from=%s  to=%s", call_sid, caller, called)

    host = request.host
    twiml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<Response>\n"
        "  <Connect>\n"
        f'    <Stream url="wss://{host}/media-stream" track="both_tracks">\n'
        f'      <Parameter name="caller"   value="{caller}"/>\n'
        f'      <Parameter name="call_sid" value="{call_sid}"/>\n'
        "    </Stream>\n"
        "  </Connect>\n"
        "</Response>"
    )
    return Response(twiml, mimetype="text/xml")


# ---------------------------------------------------------------------------
# WebSocket endpoint — receives Twilio Media Stream frames
# ---------------------------------------------------------------------------

@sock.route("/media-stream")
def media_stream(ws) -> None:
    """
    One WebSocket connection per call.

    Twilio message types handled:
      connected  — handshake, logged only
      start      — stream metadata; we create one Vosk recognizer per track
      media      — audio payload; decoded, resampled, fed to Vosk
      stop       — call ended; we flush final results and clean up
    """
    logger.info("WebSocket connected")

    # Track name -> KaldiRecognizer
    recognizers: dict[str, KaldiRecognizer] = {}
    # Track name -> audioop.ratecv state (must persist between chunks)
    ratecv_states: dict[str, object] = {}

    stream_sid: str | None = None
    call_params: dict = {}

    def _make_recognizer(track: str) -> None:
        rec = KaldiRecognizer(get_model(), VOSK_SAMPLE_RATE)
        rec.SetWords(True)
        recognizers[track] = rec
        ratecv_states[track] = None

    def _flush(track: str) -> None:
        text = json.loads(recognizers[track].FinalResult()).get("text", "").strip()
        if text:
            logger.info(
                "[FINAL][%s]  caller=%s  text=%s",
                track, call_params.get("caller", "?"), text,
            )

    try:
        while True:
            raw = ws.receive()
            if raw is None:
                break

            msg = json.loads(raw)
            event: str = msg.get("event", "")

            if event == "connected":
                logger.info(
                    "Media stream connected  protocol=%s  version=%s",
                    msg.get("protocol"), msg.get("version"),
                )

            elif event == "start":
                meta = msg["start"]
                stream_sid = meta["streamSid"]
                call_params = meta.get("customParameters", {})
                tracks: list[str] = meta.get("tracks", ["inbound_track"])
                logger.info(
                    "Stream started  sid=%s  caller=%s  call_sid=%s  tracks=%s",
                    stream_sid,
                    call_params.get("caller", "?"),
                    call_params.get("call_sid", "?"),
                    tracks,
                )
                for track in tracks:
                    _make_recognizer(track)

            elif event == "media":
                media = msg["media"]
                track: str = media.get("track", "inbound_track")

                # Lazily create recognizer if Twilio sends an unlisted track
                if track not in recognizers:
                    _make_recognizer(track)

                # 1. base64 decode -> raw μ-law bytes
                mulaw_bytes = base64.b64decode(media["payload"])
                # 2. μ-law -> signed 16-bit PCM (still at 8 000 Hz)
                pcm_8k = audioop.ulaw2lin(mulaw_bytes, 2)
                # 3. upsample 8 000 Hz -> 16 000 Hz
                pcm_16k, ratecv_states[track] = audioop.ratecv(
                    pcm_8k, 2, 1,
                    TWILIO_SAMPLE_RATE, VOSK_SAMPLE_RATE,
                    ratecv_states[track],
                )

                rec = recognizers[track]
                if rec.AcceptWaveform(pcm_16k):
                    text = json.loads(rec.Result()).get("text", "").strip()
                    if text:
                        logger.info(
                            "[TRANSCRIPT][%s]  caller=%s  text=%s",
                            track, call_params.get("caller", "?"), text,
                        )
                else:
                    partial = json.loads(rec.PartialResult()).get("partial", "")
                    if partial:
                        logger.debug("[PARTIAL][%s]  %s", track, partial)

            elif event == "stop":
                logger.info("Stream stopping  sid=%s", stream_sid)
                for track in list(recognizers):
                    _flush(track)
                break

    except Exception:
        logger.exception("Unhandled error in media stream  sid=%s", stream_sid)

    finally:
        recognizers.clear()
        logger.info("Media stream closed  sid=%s", stream_sid)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    logger.info("Starting Twilio-Vosk server on port %d", port)
    # flask dev server — use gunicorn/uvicorn in production
    app.run(host="0.0.0.0", port=port)
