# Kokoro engine: Kokoro-82M (hexgrad), the "fast" mode of the unified server.
# 82M params, <1GB VRAM, way faster than real time — no cloning, fixed voice
# catalog. One KPipeline per language, lazily created and cached. Voices are
# selected through the existing xtts_speaker param (e.g. "af_heart").

import os
import re
import tempfile
import uuid
import time

from .base import BaseEngine

# Unified-server lang codes -> Kokoro pipeline lang codes
LANG_CODES = {
    "en": "a",       # American English
    "en-gb": "b",    # British English
    "es": "e",
    "fr": "f",
    "hi": "h",
    "it": "i",
    "ja": "j",
    "pt": "p",       # Brazilian Portuguese
    "zh": "z",
}

# Default voice per pipeline lang code (used when the requested voice's
# prefix doesn't match the language, e.g. xtts_speaker=af_heart with lang=fr)
DEFAULT_VOICES = {
    "a": "af_heart",
    "b": "bf_emma",
    "e": "ef_dora",
    "f": "ff_siwis",
    "h": "hf_alpha",
    "i": "if_sara",
    "j": "jf_alpha",
    "p": "pf_dora",
    "z": "zf_xiaobei",
}

# A Kokoro voice name is "<lang_code><gender>_<name>", e.g. af_heart, ff_siwis.
# Used to tell a real voice from a leftover value of another engine ("nicole",
# "Claribel Dervla"...), which would make the pipeline raise.
VOICE_RE = re.compile(r"^[abefhijpz][fm]_")

# Cross-language voices (e.g. af_heart on French text) are allowed by default:
# the phonemization stays that of the requested language, only the timbre comes
# from the other language's voice. Set KOKORO_STRICT_VOICES=true to force every
# voice back to its language default instead.
STRICT_VOICES = os.environ.get("KOKORO_STRICT_VOICES", "false").lower() in ("1", "true")

# Curated subset of the 54 shipped voices (full list on hf.co/hexgrad/Kokoro-82M)
KNOWN_VOICES = [
    # American female / male
    "af_heart", "af_bella", "af_nicole", "af_aoede", "af_kore", "af_sarah", "af_sky",
    "am_fenrir", "am_michael", "am_puck", "am_adam", "am_onyx",
    # British female / male
    "bf_emma", "bf_isabella", "bm_george", "bm_fable",
    # Other languages
    "ef_dora", "em_alex", "ff_siwis", "if_sara", "im_nicola",
    "jf_alpha", "jm_kumo", "pf_dora", "pm_alex", "zf_xiaobei", "zm_yunjian",
]


class KokoroEngine(BaseEngine):
    id = "kokoro"
    label = "Kokoro-82M (fast)"
    lightweight = True

    def __init__(self):
        # lang_code -> KPipeline, lazily created
        self.pipelines = {}
        self._device = None

    def available(self):
        try:
            import kokoro  # noqa: F401
            return (True, "")
        except Exception as err:
            return (False, f"kokoro not installed ({err.__class__.__name__})")

    def loaded_models(self):
        return [f"kokoro:{code}" for code in self.pipelines]

    def unload_all(self):
        if not self.pipelines:
            return
        import gc
        import torch
        self.pipelines.clear()
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("[kokoro] pipelines unloaded")

    def _get_device(self):
        if self._device is None:
            import torch
            override = os.environ.get("KOKORO_DEVICE") or os.environ.get("TTS_DEVICE")
            self._device = override or ("cuda" if torch.cuda.is_available() else "cpu")
            print(f"[kokoro] device: {self._device}")
        return self._device

    def _get_pipeline(self, lang_code):
        if lang_code not in self.pipelines:
            from kokoro import KPipeline
            t0 = time.perf_counter()
            self.pipelines[lang_code] = KPipeline(
                lang_code=lang_code,
                repo_id="hexgrad/Kokoro-82M",
                device=self._get_device(),
            )
            print(f"[kokoro] pipeline '{lang_code}' ready ({time.perf_counter() - t0:.1f}s)")
        return self.pipelines[lang_code]

    def synthesize(self, job):
        import numpy as np
        import soundfile as sf

        text = job["text"]
        lang = (job.get("lang") or "en").lower()
        data = job.get("data") or {}

        lang_code = LANG_CODES.get(lang, "a")

        # Voice: reuse the xtts_speaker param. Fall back to the language's default
        # when empty or when the value isn't a Kokoro voice at all (leftover from
        # another engine). A voice from ANOTHER language is passed through — the
        # text is still phonemized in `lang`, only the timbre is foreign — unless
        # KOKORO_STRICT_VOICES is set.
        voice = job.get("xtts_speaker") or DEFAULT_VOICES[lang_code]
        if not VOICE_RE.match(voice):
            print(f"[kokoro] '{voice}' is not a Kokoro voice, "
                  f"using {DEFAULT_VOICES[lang_code]}")
            voice = DEFAULT_VOICES[lang_code]
        elif not voice.startswith(lang_code):
            if STRICT_VOICES:
                print(f"[kokoro] voice '{voice}' doesn't match lang '{lang}', "
                      f"using {DEFAULT_VOICES[lang_code]} (strict mode)")
                voice = DEFAULT_VOICES[lang_code]
            else:
                print(f"[kokoro] cross-language voice: '{voice}' on lang '{lang}'")

        speed = float(data.get("speed", 1.0))

        pipeline = self._get_pipeline(lang_code)
        print(f"[kokoro] generating: lang={lang_code}, voice={voice}, speed={speed}")

        t0 = time.perf_counter()
        # The pipeline yields one chunk per split segment; concatenate them all
        chunks = [result.audio.numpy() for result in pipeline(text, voice=voice, speed=speed)]
        if not chunks:
            raise RuntimeError("kokoro produced no audio")
        audio = np.concatenate(chunks)
        print(f"[kokoro] generated in {time.perf_counter() - t0:.2f}s ({len(text)} chars)")

        tmp_wav = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.wav")
        sf.write(tmp_wav, audio, 24000)
        return tmp_wav

    def voices(self):
        return {
            "modes": ["fast"],
            "kokoro_voices": KNOWN_VOICES,
            "languages": sorted(LANG_CODES.keys()),
            "default": "af_heart",
        }
