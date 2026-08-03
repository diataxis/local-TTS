# Chatterbox engine: turbo / standard / multilingual sub-models.
# Faithful port of the local-tts-chatterbox server.py, wrapped as an engine:
# lazy model loading with LRU eviction, voice-embedding cache, and the same
# post-load optimizations (TF32, flatten_parameters, weight_norm removal...).

import os
import gc
import time
import tempfile
import uuid
from collections import OrderedDict

from .base import BaseEngine

VOICES_DIR = "./voices"
PRESETS_DIR = "./voices/presets"
MY_VOICES_DIR = "./voices/my_voices"


class ChatterboxEngine(BaseEngine):
    id = "chatterbox"
    label = "Chatterbox (Resemble AI)"

    def __init__(self):
        # Lazy-loaded sub-model cache (LRU-ordered): turbo / standard / multilingual
        self.models = OrderedDict()
        self.max_models = int(os.environ.get("CHATTERBOX_MAX_MODELS", "1"))
        # Voice embedding cache: (model_type, abs_path, mtime) -> model.conds
        self._voice_cache = OrderedDict()
        self._voice_cache_max = int(os.environ.get("CHATTERBOX_VOICE_CACHE", "16"))
        self._env_ready = False
        self._device = None

    def available(self):
        try:
            import chatterbox  # noqa: F401
            return (True, "")
        except Exception as err:
            return (False, f"chatterbox-tts not installed ({err.__class__.__name__})")

    def loaded_models(self):
        return list(self.models.keys())

    # ----- environment ------------------------------------------------------

    def _setup_env(self):
        """One-time torch/perth setup, deferred until the engine is first used."""
        if self._env_ready:
            return
        import torch

        torch.set_float32_matmul_precision("high")

        # Apple Silicon fix: resemble-perth watermarker has no ARM binary
        import perth
        if perth.PerthImplicitWatermarker is None:
            print("[chatterbox] patching perth: DummyWatermarker (no ARM binary)")
            perth.PerthImplicitWatermarker = perth.DummyWatermarker

        override = os.environ.get("CHATTERBOX_DEVICE") or os.environ.get("TTS_DEVICE")
        if override:
            self._device = override
        elif torch.cuda.is_available():
            self._device = "cuda"
            print("[chatterbox] GPU:", torch.cuda.get_device_name(torch.cuda.current_device()))
        else:
            self._device = "cpu"
        print(f"[chatterbox] device: {self._device}")
        self._env_ready = True

    def _free_memory(self):
        import torch
        gc.collect()
        if self._device == "cuda":
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
        elif self._device == "mps":
            try:
                torch.mps.empty_cache()
            except Exception:
                pass

    # ----- model management -------------------------------------------------

    def _unload_model(self, model_type):
        model = self.models.pop(model_type, None)
        if model is None:
            return
        # Drop voice-cache entries referencing this model's tensors
        for key in [k for k in self._voice_cache if k[0] == model_type]:
            del self._voice_cache[key]
        try:
            model.to("cpu")
        except Exception:
            pass
        del model
        self._free_memory()
        print(f"[chatterbox] unloaded {model_type} model")

    def unload_all(self):
        for model_type in list(self.models.keys()):
            self._unload_model(model_type)

    def _optimize_model(self, model, model_type):
        import torch
        try:
            model.ve.lstm.flatten_parameters()
            print("  + LSTM flatten_parameters")
        except Exception as e:
            print(f"  - LSTM flatten_parameters failed: {e}")

        try:
            vocoder = model.s3gen.mel2wav
            from torch.nn.utils.parametrize import remove_parametrizations
            count = 0
            for module in vocoder.modules():
                if hasattr(module, "parametrizations") and hasattr(module.parametrizations, "weight"):
                    remove_parametrizations(module, "weight")
                    count += 1
            print(f"  + HiFiGAN weight_norm removed ({count} layers)")
        except Exception as e:
            print(f"  - HiFiGAN weight_norm removal failed: {e}")

        if os.environ.get("CHATTERBOX_DTYPE", "") == "float16":
            try:
                model.half()
                print("  + Converted to float16")
            except Exception as e:
                print(f"  - float16 conversion failed: {e}")

        if os.environ.get("CHATTERBOX_COMPILE", "").lower() in ("1", "true"):
            try:
                model.t3.tfmr = torch.compile(model.t3.tfmr)
                print("  + torch.compile on T3 transformer (first call will be slow)")
            except Exception as e:
                print(f"  - torch.compile failed: {e}")

    def get_model(self, model_type="turbo"):
        import torch
        self._setup_env()

        if model_type in self.models:
            self.models.move_to_end(model_type)
            return self.models[model_type]

        while len(self.models) >= self.max_models:
            oldest = next(iter(self.models))
            self._unload_model(oldest)

        t0 = time.perf_counter()
        if model_type == "turbo":
            from chatterbox.tts_turbo import ChatterboxTurboTTS
            self.models[model_type] = ChatterboxTurboTTS.from_pretrained(device=self._device)
        elif model_type == "standard":
            from chatterbox.tts import ChatterboxTTS
            self.models[model_type] = ChatterboxTTS.from_pretrained(device=self._device)
        elif model_type == "multilingual":
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS
            # Multilingual checkpoint saved with CUDA tensors — force map_location
            _orig_load = torch.load
            torch.load = lambda *a, **kw: _orig_load(*a, **{**kw, "map_location": self._device})
            try:
                self.models[model_type] = ChatterboxMultilingualTTS.from_pretrained(device=self._device)
            finally:
                torch.load = _orig_load
        else:
            raise ValueError(f"Unknown model_type: {model_type}")

        print(f"[chatterbox] loaded {model_type} on {self._device} ({time.perf_counter() - t0:.1f}s)")
        self._optimize_model(self.models[model_type], model_type)
        return self.models[model_type]

    # ----- voice resolution -------------------------------------------------

    def _prepare_voice(self, model, model_type, audio_prompt_path):
        """Prepare voice conditionals with caching. True if conditionals are ready."""
        if not audio_prompt_path:
            return False
        abs_path = os.path.abspath(audio_prompt_path)
        try:
            mtime = os.path.getmtime(abs_path)
        except OSError:
            return False

        cache_key = (model_type, abs_path, mtime)
        if cache_key in self._voice_cache:
            model.conds = self._voice_cache[cache_key]
            self._voice_cache.move_to_end(cache_key)
            print(f"  voice cache HIT: {os.path.basename(abs_path)}")
            return True

        t0 = time.perf_counter()
        model.prepare_conditionals(abs_path)
        self._voice_cache[cache_key] = model.conds
        self._voice_cache.move_to_end(cache_key)
        while len(self._voice_cache) > self._voice_cache_max:
            self._voice_cache.popitem(last=False)
        print(f"  voice cache MISS: {os.path.basename(abs_path)} ({time.perf_counter() - t0:.2f}s)")
        return True

    def resolve_audio_prompt(self, tts_voice, xtts_speaker):
        """Map (tts_voice, xtts_speaker) to a reference WAV path."""
        if tts_voice == "cloning":
            if xtts_speaker:
                for directory in [MY_VOICES_DIR, PRESETS_DIR]:
                    for name in [xtts_speaker, f"{xtts_speaker}.wav"]:
                        path = os.path.join(directory, name)
                        if os.path.exists(path):
                            return path
                return os.path.join(MY_VOICES_DIR, xtts_speaker)
            return None

        # standard / gpu1 / turbo... : nicole by default, else presets then uploads
        if xtts_speaker == "nicole" or xtts_speaker is None:
            return f"{VOICES_DIR}/nicole.wav"
        for directory in [PRESETS_DIR, MY_VOICES_DIR]:
            for name in [xtts_speaker, f"{xtts_speaker}.wav"]:
                path = os.path.join(directory, name)
                if os.path.exists(path):
                    return path
        return f"{VOICES_DIR}/nicole.wav"

    # ----- synthesis --------------------------------------------------------

    def synthesize(self, job):
        import torch
        import torchaudio

        text = job["text"]
        tts_voice = job["tts_voice"]
        xtts_speaker = job.get("xtts_speaker")
        lang = job.get("lang") or "en"
        data = job.get("data") or {}

        exaggeration = data.get("exaggeration", 0.5)
        cfg_weight = data.get("cfg_weight", 0.5)

        audio_prompt_path = self.resolve_audio_prompt(tts_voice, xtts_speaker)
        if audio_prompt_path and not os.path.exists(audio_prompt_path):
            print(f"[chatterbox] audio prompt not found: {audio_prompt_path}")
            audio_prompt_path = None

        # Model selection: multilingual for non-English, "standard" on request
        # (fine control via exaggeration/cfg_weight), turbo for everything else.
        if lang and lang != "en":
            model_type = "multilingual"
            generate_kwargs = {
                "text": text,
                "language_id": lang,
                "exaggeration": exaggeration,
                "cfg_weight": cfg_weight,
            }
        elif tts_voice == "standard":
            model_type = "standard"
            generate_kwargs = {
                "text": text,
                "exaggeration": exaggeration,
                "cfg_weight": cfg_weight,
            }
        else:
            model_type = "turbo"
            generate_kwargs = {"text": text}

        model = self.get_model(model_type)
        voice_cached = self._prepare_voice(model, model_type, audio_prompt_path)
        if audio_prompt_path and not voice_cached:
            generate_kwargs["audio_prompt_path"] = audio_prompt_path

        print(f"[chatterbox] generating: model={model_type}, tts_voice={tts_voice}, "
              f"lang={lang}, speaker={xtts_speaker}")

        t0 = time.perf_counter()
        with torch.inference_mode():
            wav = model.generate(**generate_kwargs)
        print(f"[chatterbox] generated in {time.perf_counter() - t0:.2f}s ({len(text)} chars)")

        tmp_wav = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.wav")
        torchaudio.save(tmp_wav, wav, model.sr)
        return tmp_wav

    def voices(self):
        presets = []
        if os.path.exists(PRESETS_DIR):
            presets = sorted([
                f for f in os.listdir(PRESETS_DIR)
                if f.endswith((".wav", ".mp3")) and not f.startswith(".")
            ])
        return {
            "modes": ["standard", "turbo", "cloning"],
            "presets": presets,
            "default": "nicole.wav",
        }
