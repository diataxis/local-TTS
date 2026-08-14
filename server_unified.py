# Unified local TTS server for eu.daimonia.app
#
# One server, several engines (Coqui VITS/xTTSv2 + Chatterbox, extensible).
# Same HTTP contract as the two legacy servers (server.py of local-TTS and of
# local-tts-chatterbox), so existing frontends work without any change:
#
#   POST /tts     {text, tts_voice, xtts_speaker, lang, [engine], [exaggeration], [cfg_weight]}
#                 -> WAV file
#   POST /upload  multipart file -> {filename, success}   (voice cloning samples)
#   GET  /voices  -> voice catalog per engine
#   GET  /health  -> engines availability + loaded models
#
# Routing: tts_voice cpu1/gpu1/cloning -> Coqui, standard -> Chatterbox.
# The optional "engine" param overrides this (e.g. engine: "chatterbox" with
# tts_voice: "cloning" for Chatterbox voice cloning). If the routed engine's
# dependencies aren't installed, the request falls back to whichever engine is
# available — a Coqui-only or Chatterbox-only install keeps working like the
# legacy single servers did.
#
# Start:  uvicorn server_unified:app --host 0.0.0.0 --port 3200

import os
import shutil

from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from engines import ENGINES, pick_engine, unload_others, EXCLUSIVE

MY_VOICES_DIR = "./voices/my_voices"
PRESETS_DIR = "./voices/presets"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.middleware("http")
async def add_custom_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response


@app.post("/tts")
async def generate_tts(request: Request):
    data = await request.json()
    text = (data.get("text") or "").strip()
    if not text:
        return JSONResponse(content={"error": "No text provided"}, status_code=400)

    engine, error = pick_engine(data)
    if engine is None:
        return JSONResponse(content={"error": error}, status_code=400)

    ok, reason = engine.available()
    if not ok:
        return JSONResponse(
            content={"error": f"Engine '{engine.id}' unavailable: {reason}"},
            status_code=503,
        )

    unload_others(engine)

    job = {
        "text": text,
        "tts_voice": data.get("tts_voice") or "gpu1",
        "xtts_speaker": data.get("xtts_speaker"),
        "lang": data.get("lang") or "en",
        "data": data,
    }
    print(f"[TEXT]:: {job['text']}\n\n"
        f"[tts] engine={engine.id} tts_voice={job['tts_voice']} "
          f"speaker={job['xtts_speaker']} lang={job['lang']}")

    try:
        tmp_wav = engine.synthesize(job)
    except Exception as err:
        print(f"[tts] engine '{engine.id}' error: {err}")
        return JSONResponse(
            content={"error": f"Engine '{engine.id}' failed: {err}"},
            status_code=500,
        )

    return FileResponse(tmp_wav, media_type="audio/wav", filename="speech.wav")


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    print("[upload]", file.filename)
    os.makedirs(MY_VOICES_DIR, exist_ok=True)
    file_location = os.path.join(MY_VOICES_DIR, file.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return JSONResponse(content={"filename": file.filename, "success": True})


@app.get("/voices")
async def list_voices():
    """Voice catalog. Keeps the legacy chatterbox keys (presets / my_voices /
    default) and adds a per-engine breakdown."""
    my_voices = []
    if os.path.exists(MY_VOICES_DIR):
        my_voices = sorted([
            f for f in os.listdir(MY_VOICES_DIR)
            if f.endswith((".wav", ".mp3")) and not f.startswith(".")
        ])
    presets = []
    if os.path.exists(PRESETS_DIR):
        presets = sorted([
            f for f in os.listdir(PRESETS_DIR)
            if f.endswith((".wav", ".mp3")) and not f.startswith(".")
        ])

    engines_block = {}
    for engine in ENGINES.values():
        ok, reason = engine.available()
        engines_block[engine.id] = {
            "label": engine.label,
            "available": ok,
            "reason": reason,
            "voices": engine.voices() if ok else {},
        }

    return JSONResponse(content={
        "presets": presets,
        "my_voices": my_voices,
        "default": "nicole.wav",
        "engines": engines_block,
    })


@app.get("/health")
async def health():
    engines_block = {}
    for engine in ENGINES.values():
        ok, reason = engine.available()
        engines_block[engine.id] = {
            "label": engine.label,
            "available": ok,
            "reason": reason,
            "loaded_models": engine.loaded_models(),
        }
    return JSONResponse(content={
        "status": "ok",
        "exclusive_memory": EXCLUSIVE,
        "engines": engines_block,
    })


@app.on_event("startup")
async def startup():
    print("=== Unified TTS server ===")
    try:
        import torch
        print("GPU", torch.cuda.is_available())
        if torch.cuda.is_available():
            print("CUDA Version", torch.version.cuda)
            print("GPU", torch.cuda.get_device_name(torch.cuda.current_device()))
    except Exception as err:
        print(f"torch not importable: {err}")

    for engine in ENGINES.values():
        ok, reason = engine.available()
        print(f"engine {engine.id:<12} {'OK' if ok else 'UNAVAILABLE (' + reason + ')'}")

    # Optional model preload, e.g. TTS_PRELOAD=chatterbox:turbo or TTS_PRELOAD=coqui:gpu1
    preload = os.environ.get("TTS_PRELOAD", "")
    for item in [p.strip() for p in preload.split(",") if p.strip()]:
        engine_id, _, model_ref = item.partition(":")
        engine = ENGINES.get(engine_id)
        if engine is None or not engine.available()[0]:
            print(f"[preload] skipping '{item}' (engine unavailable)")
            continue
        print(f"[preload] {item}...")
        try:
            if engine_id == "chatterbox":
                engine.get_model(model_ref or "turbo")
            else:
                # Warm the model with a silent dummy call path: just load it
                engine.synthesize({
                    "text": "warmup",
                    "tts_voice": model_ref or "gpu1",
                    "xtts_speaker": None,
                    "lang": "en",
                    "data": {},
                })
        except Exception as err:
            print(f"[preload] '{item}' failed: {err}")
