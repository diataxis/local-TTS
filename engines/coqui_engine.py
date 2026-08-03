# Coqui engine: VITS (cpu1) + xTTSv2 (gpu1 / cloning).
# Faithful port of the legacy server.py behavior (same presets, same
# speaker/cloning resolution, same short-text handling, same sampling params).

import os
import tempfile
import uuid

from .base import BaseEngine

VOICES_DIR = "./voices"
MY_VOICES_DIR = "./voices/my_voices"

# Same presets as the legacy presets.py (kept here so the legacy files stay untouched)
PRESETS = {
    "cpu1": {
        "model": "tts_models/en/vctk/vits",
        "settings": {
            "speaker": "p294",
            "length_scale": 1.1,
            "noise_scale": 0.33,
            "noise_w": 0.8,
        },
    },
    "gpu1": {
        "model": "tts_models/multilingual/multi-dataset/xtts_v2",
        "settings": {
            "language": "en",
            "speaker_wav": [f"{VOICES_DIR}/nicole.wav"],
        },
    },
    "cloning": {
        "model": "tts_models/multilingual/multi-dataset/xtts_v2",
        "settings": {
            "language": "en",
            "speaker_wav": [f"{VOICES_DIR}/nicole.wav"],
        },
    },
}


class CoquiEngine(BaseEngine):
    id = "coqui"
    label = "Coqui (VITS / xTTSv2)"

    def __init__(self):
        self.model = None
        self.current_model_name = ""

    def available(self):
        try:
            import TTS.api  # noqa: F401
            return (True, "")
        except Exception as err:
            return (False, f"coqui-tts not installed ({err.__class__.__name__})")

    def loaded_models(self):
        return [self.current_model_name] if self.model else []

    def unload_all(self):
        if self.model is None:
            return
        import gc
        import torch
        model = self.model
        self.model = None
        self.current_model_name = ""
        del model
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        print("[coqui] model unloaded")

    def _device(self):
        import torch
        override = os.environ.get("TTS_DEVICE")
        if override:
            return override
        return "cuda" if torch.cuda.is_available() else "cpu"

    def synthesize(self, job):
        from TTS.api import TTS

        text = job["text"]
        tts_voice = job["tts_voice"]
        xtts_speaker = job.get("xtts_speaker")
        lang = job.get("lang") or "en"

        # Unknown modes (e.g. "standard" reaching us through the fallback
        # when Chatterbox isn't installed) are served with xTTSv2.
        if tts_voice not in PRESETS:
            print(f"[coqui] unknown tts_voice '{tts_voice}', using gpu1 (xTTSv2)")
            tts_voice = "gpu1"

        preset = PRESETS[tts_voice]

        if self.model is None or preset["model"] != self.current_model_name:
            print(f"[coqui] loading model {preset['model']}")
            self.model = TTS(model_name=preset["model"], progress_bar=True).to(self._device())
            self.current_model_name = preset["model"]

        # Fresh copy per request (the legacy server mutated the shared preset dict)
        settings = dict(preset["settings"])

        # Speaker / cloning resolution — identical to the legacy server
        if tts_voice == "gpu1" and xtts_speaker == "nicole":
            settings["speaker"] = None
            settings["speaker_wav"] = [f"{VOICES_DIR}/nicole.wav"]
        elif tts_voice == "cloning":
            settings["speaker"] = None
            settings["speaker_wav"] = [os.path.join(MY_VOICES_DIR, xtts_speaker or "")]
        elif xtts_speaker is not None and xtts_speaker != "nicole":
            settings["speaker"] = xtts_speaker
            settings["speaker_wav"] = None

        if tts_voice in ("gpu1", "cloning"):
            settings["language"] = lang

        settings["text"] = text
        tmp_wav = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.wav")
        settings["file_path"] = tmp_wav

        # Short texts: avoid sentence splitting artifacts on xTTSv2
        settings["split_sentences"] = True
        if len(text.split()) <= 3 and tts_voice in ("gpu1", "cloning"):
            print("[coqui] short text, disabling sentence splitting")
            settings["split_sentences"] = False

        self.model.tts_to_file(
            **settings,
            temperature=0.7,
            top_p=0.85,
        )
        return tmp_wav

    def voices(self):
        try:
            from xtts_speakers import speakers as xtts_speakers
        except Exception:
            xtts_speakers = []
        try:
            from vits_speakers import vits_speakers
        except Exception:
            vits_speakers = []
        return {
            "modes": ["cpu1", "gpu1", "cloning"],
            "xtts_speakers": xtts_speakers,
            "vits_speakers": vits_speakers,
            "cloning_extra": ["nicole"],
        }
