# Base class for all TTS engines of the unified server.
# An engine wraps one TTS technology (Coqui VITS/xTTSv2, Chatterbox, ...).
# Heavy libraries must ONLY be imported inside methods (lazy imports), so the
# server can start and route even when an engine's dependencies are missing.


class BaseEngine:
    # Unique id used in the "engine" request param and in /health
    id = "base"
    label = "Base engine"
    # Lightweight engines (<1GB VRAM) are exempt from TTS_EXCLUSIVE eviction:
    # they never evict the heavy engines and are never evicted by them.
    lightweight = False

    def available(self):
        """Return (True, "") if the engine's dependencies are installed,
        else (False, reason). Must be cheap and never raise."""
        return (False, "not implemented")

    def loaded_models(self):
        """List of model names currently resident in memory (for /health)."""
        return []

    def unload_all(self):
        """Fully release every loaded model (used for VRAM exclusivity
        when switching engines)."""
        pass

    def synthesize(self, job):
        """Generate speech and return the path of a WAV file.

        job is a dict with at least:
          text          - text to speak (non empty, stripped)
          tts_voice     - legacy mode selector (cpu1 / gpu1 / cloning / standard / ...)
          xtts_speaker  - speaker name, preset name or uploaded filename
          lang          - language code ("en" default)
          data          - the full raw request body (for engine-specific params)
        """
        raise NotImplementedError

    def voices(self):
        """Describe the voices this engine can serve (for /voices)."""
        return {}
