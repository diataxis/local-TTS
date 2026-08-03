# Engine registry + request routing for the unified TTS server.
#
# Adding a new TTS technology = add a module with a BaseEngine subclass,
# register it in ENGINES below, and (optionally) claim tts_voice values
# in VOICE_ROUTES. Nothing else to change.

import os

from .coqui_engine import CoquiEngine
from .chatterbox_engine import ChatterboxEngine
from .kokoro_engine import KokoroEngine

ENGINES = {}
for _engine in (CoquiEngine(), ChatterboxEngine(), KokoroEngine()):
    ENGINES[_engine.id] = _engine

# Legacy tts_voice values -> default engine.
# cpu1/gpu1/cloning historically mean Coqui, standard means Chatterbox.
VOICE_ROUTES = {
    "cpu1": "coqui",
    "gpu1": "coqui",
    "cloning": "coqui",
    "standard": "chatterbox",
    "turbo": "chatterbox",
    "fast": "kokoro",
}

# When true (default), synthesizing with one engine unloads the others first.
# Both stacks target ~4GB VRAM GPUs, they generally can't coexist.
EXCLUSIVE = os.environ.get("TTS_EXCLUSIVE", "true").lower() not in ("0", "false")


def pick_engine(data):
    """Choose the engine for a /tts request.

    Priority:
      1. explicit "engine" param (no fallback — an unknown id is an error)
      2. legacy tts_voice mapping (VOICE_ROUTES)
      3. if the mapped engine's dependencies are missing, fall back to any
         available engine — this preserves the old single-server installs
         (e.g. a Chatterbox-only install keeps serving cpu1/gpu1/cloning,
         exactly like the legacy chatterbox server did).

    Returns (engine, error_message). engine is None on unknown "engine" param.
    """
    requested = data.get("engine")
    if requested:
        engine = ENGINES.get(requested)
        if engine is None:
            return None, f"Unknown engine '{requested}'. Known: {list(ENGINES.keys())}"
        return engine, None

    tts_voice = data.get("tts_voice") or "gpu1"
    primary_id = VOICE_ROUTES.get(tts_voice, "coqui")
    primary = ENGINES[primary_id]

    ok, reason = primary.available()
    if ok:
        return primary, None

    for other in ENGINES.values():
        if other is not primary and other.available()[0]:
            print(f"[router] engine '{primary_id}' unavailable ({reason}) "
                  f"-> falling back to '{other.id}'")
            return other, None

    # Nothing available: return the primary so the caller reports its reason
    return primary, None


def unload_others(active_engine):
    """Free the memory of every engine except the active one.
    Lightweight engines (e.g. Kokoro) neither evict nor get evicted."""
    if not EXCLUSIVE or active_engine.lightweight:
        return
    for engine in ENGINES.values():
        if engine is not active_engine and not engine.lightweight and engine.loaded_models():
            print(f"[router] exclusive mode: unloading engine '{engine.id}'")
            engine.unload_all()
