# local-TTS

Local TTS server for [eu.daimonia.app](https://eu.daimonia.app) — **one server, several
TTS engines**.

| Engine | What it gives you | Hardware |
|---|---|---|
| **VITS** (Coqui) | Fast, light, robotic. 100+ English voices | CPU only, no GPU needed |
| **xTTSv2** (Coqui) | Good quality, 58 built-in voices, 15 languages | GPU ~4GB VRAM |
| **xTTSv2 cloning** | Clone any voice from an audio sample | GPU ~4GB VRAM, slower |
| **Chatterbox** (Resemble AI) | The most natural and expressive voices, cloning + narrator | GPU |
| **Kokoro-82M** (hexgrad) | Near-instant generation, 54 clean voices, 9 languages (no cloning) | GPU <1GB VRAM or CPU |

All of them are served by the same process, on the same API, at
`http://localhost:3200`. You install only what you want to use: the server detects
which engines are available and routes accordingly.

A full guide with videos is available here:
https://eu.daimonia.app/articles/local-TTS

---

## Getting started

### 1. Miniconda

Install miniconda from https://www.anaconda.com/download/success

### 2. Windows: the batch files

Two `.bat` files at the root of the folder do everything for you:

```bash
installation_unified.bat        # installs everything (creates the conda env)
start_server_unified.bat        # starts the server
```

`installation_unified.bat` takes an optional argument to pick the PyTorch build:

```bash
installation_unified.bat cu124      # NVIDIA GPU (default)
installation_unified.bat cu126      # NVIDIA GPU, CUDA 12.6
installation_unified.bat cpu        # no GPU
```

Make sure to change the following line in both files to the path where Conda is
installed on your machine:

```bash
set "CONDA_PATH=[CONDA_PATH]"
```

You can find that path with `conda info` (line: "base environment").

> Thanks to Senorgif, who created the original batch files.

### 3. Manual installation

If the batch files fail, or if you're on Linux/macOS, follow these steps.

Open a terminal and create the environment (**Python 3.11**):

```bash
conda create -n local-tts-unified python=3.11 -y
conda activate local-tts-unified
```

**Install PyTorch first**, with the build matching your hardware:

```bash
# NVIDIA GPU (CUDA 12.4)
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124

# CPU only
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu
```

Then the engines (see `requirements_unified.txt`, which contains the same steps
with comments):

```bash
# Coqui — VITS + xTTSv2
# (drop the [languages] extra if gruut/mecab fail to build: they are only needed for ja/zh)
pip install "coqui-tts[languages]"

# Chatterbox
pip install diffusers==0.29.0 conformer==0.3.2 resemble-perth==1.0.1 librosa==0.11.0 pykakasi==2.3.0
pip install onnx==1.16.2
pip install --no-deps s3tokenizer==0.2.0
pip install --no-deps chatterbox-tts
pip install pyloudnorm omegaconf

# API
pip install fastapi==0.110.1 uvicorn==0.29.0 python-multipart==0.0.9 pydub==0.25.1

# IMPORTANT — install this LAST (see "Troubleshooting" below)
pip install transformers==4.57.1
```

> **espeak-ng** is required by the VITS (CPU) engine. If you get an `espeak`
> error, install it from
> https://github.com/espeak-ng/espeak-ng/blob/master/docs/guide.md then restart
> your computer so the PATH is updated.

### 4. Start the server

```bash
uvicorn server_unified:app --host 0.0.0.0 --port 3200
```

Then set the TTS server URL in Eudaimonia to `http://localhost:3200`.

Check that everything is detected by opening http://localhost:3200/health — you
should see `"available": true` for the engines you installed.

> The **first** request with a given engine/voice takes a while: the model has to
> be downloaded, then loaded into memory. For xTTSv2 you also have to accept the
> Coqui licence in the terminal on first use.

---

## Using it from Eudaimonia

In the app's voice settings, pick **Local**, set the server URL, then pick an
engine. The app talks to `/health` and `/voices`, so:

- engines that aren't installed are flagged in the dropdown,
- Chatterbox voices are read from your `voices/presets/` folder,
- your own uploaded voices appear under "Your uploaded voices".

The **narrator** (a second voice for the `*narration*` parts) works with every
engine.

---

## Upgrading / compatibility

**The API contract has not changed.** If you already run an older server — the
previous `local-TTS` (Coqui) one, or the separate `local-TTS-Chatterbox` one —
**you don't have to update anything**. Eudaimonia keeps working with it exactly
as before.

| Your server | Works with the app | What you get |
|---|---|---|
| **Unified server** (this repo) | ✅ | Everything: all engines at once, engine detection, server-side voice list |
| Old **local-TTS** (Coqui) server | ✅ | VITS, xTTSv2, cloning. Chatterbox is not available on that server |
| Old **Chatterbox** server | ✅ | Chatterbox voices, cloning, narrator, and the voice list from your `presets/` folder |

What you miss by staying on an old server is only comfort: the app can't show
which engines are installed (it just says "Server online"), and for Chatterbox
it falls back to its built-in voice list instead of reading your `presets/`
folder.

> With the **old Coqui server**, picking Chatterbox in the app returns an error:
> that server doesn't know that engine. Use the Chatterbox server or this unified
> one. (This was already the case before.)

**Upgrading is non-destructive**: replace the files, keep your `voices/` folder
(your uploads in `voices/my_voices/` and your Chatterbox `voices/presets/` are
reused as-is), and your settings in the app stay valid — engine names
(`cpu1`, `gpu1`, `cloning`, `standard`) haven't changed.

---

## Voices

### Built-in voices

VITS and xTTSv2 have built-in speakers — nothing to install, just pick one in the
app.

### Chatterbox voices

Chatterbox does **voice cloning only**: every "voice" is a reference WAV in
`voices/presets/`. To add one, drop a `.wav` in that folder — it is picked up
immediately, no restart needed, and it shows up in the app.

The `voices/presets/archived/` subfolder is ignored by the server: that's where
you move the samples you don't want to offer anymore.

**What makes a good sample:** 7 to 20 seconds, a single speaker, steady delivery,
no music, no background noise, no reverb, no long silences, mono, 24kHz or more,
16-bit WAV. The filename is the name shown in the app.

You can also generate reference voices from the 58 built-in xTTSv2 speakers (handy
to get male voices quickly). With the server running:

```bash
python make_presets_from_xtts.py --male
python make_presets_from_xtts.py --female
python make_presets_from_xtts.py "Damien Black" "Craig Gutsy"
```

Listen to the results, keep the good ones, move the rest to `voices/presets/archived/`.

### Your own voices

Files uploaded from the app (`POST /upload`) land in `voices/my_voices/` and are
shared by **both** cloning engines (xTTSv2 cloning and Chatterbox).

---

## API

### `POST /tts` → WAV file

```json
{
  "text": "Close your eyes...",
  "tts_voice": "gpu1",
  "xtts_speaker": "Daisy Studious",
  "lang": "en"
}
```

| Param | Description |
|---|---|
| `text` | Text to speak |
| `tts_voice` | `cpu1` (VITS), `gpu1` (xTTSv2), `cloning` (xTTSv2 cloning), `standard` (Chatterbox), `turbo` (Chatterbox turbo), `fast` (Kokoro) |
| `xtts_speaker` | Speaker name, preset name, uploaded filename, or Kokoro voice (`af_heart`, `af_bella`...) |
| `lang` | Language code. On Chatterbox, anything other than `en` switches to its multilingual model |
| `engine` | *(optional)* Force an engine: `coqui`, `chatterbox` or `kokoro`. Overrides the routing |
| `exaggeration` / `cfg_weight` | *(optional, Chatterbox)* 0.0–1.0, emotion intensity / style adherence |
| `speed` | *(optional, Kokoro)* speech rate, default 1.0 |

**Routing:** `cpu1`/`gpu1`/`cloning` go to Coqui, `standard`/`turbo` go to
Chatterbox, `fast` goes to Kokoro. If the engine that should answer isn't installed, the request
**falls back** to one that is — so a partial install keeps working.

### `POST /upload`

Multipart file upload → saved in `voices/my_voices/`, returns
`{"filename": "...", "success": true}`.

### `GET /voices`

Lists Chatterbox reference voices (`presets`), your uploads (`my_voices`), and a
per-engine breakdown.

### `GET /health`

Engine availability (with the reason when something is missing) and the models
currently loaded. Use it to check your install.

---

## Configuration

Everything is optional — the defaults are fine for most setups.

| Variable | Effect |
|---|---|
| `TTS_DEVICE` | Force the device for every engine (`cuda`, `cpu`, `mps`) |
| `TTS_EXCLUSIVE` | `false` lets several engines stay in memory at once (default `true`) |
| `TTS_PRELOAD` | Models to load at startup, e.g. `chatterbox:turbo` (default: none, loaded on demand) |
| `CHATTERBOX_MAX_MODELS` | How many Chatterbox sub-models stay resident (default 1) |
| `CHATTERBOX_VOICE_CACHE` | Voice embedding cache size (default 16) |
| `CHATTERBOX_DTYPE` | `float16` for half precision (experimental) |
| `CHATTERBOX_COMPILE` | `true` to `torch.compile` the Chatterbox transformer (slow first call, faster after) |

By default, generating with one engine unloads the other: both target ~4GB VRAM
GPUs and generally can't coexist. Set `TTS_EXCLUSIVE=false` if you have VRAM to
spare.

---

## RunPod

If you're using an RTX 5090, start with the "RunPod PyTorch 2.8.0" template.
Otherwise "RunPod PyTorch 2.2.0" is fine.

```bash
apt update
apt-get install espeak-ng
git clone https://github.com/diataxis/local-TTS.git
cd local-TTS/
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements_unified.txt
pip install --no-deps s3tokenizer==0.2.0
pip install --no-deps chatterbox-tts
pip install transformers==4.57.1
uvicorn server_unified:app --host 0.0.0.0 --port 3200
```

---

## Troubleshooting

### `ImportError: cannot import name 'isin_mps_friendly'`

The single most important thing to know about this install:

**`transformers` must be version 4.57.1.**

`coqui-tts` declares `transformers>=4.57`, but its code uses `isin_mps_friendly`,
which was **removed in transformers 5.x** — so Coqui breaks with any 5.x version.
`chatterbox-tts` pins `transformers==5.2.0`, but actually runs fine on 4.57.1.
That makes 4.57.1 the only version that satisfies both, and it must be installed
**last**, so nothing pulls it back up:

```bash
pip install transformers==4.57.1
```

### pip warnings about chatterbox

After installing, pip prints something like:

```
chatterbox-tts 0.1.7 requires gradio==6.8.0, which is not installed.
chatterbox-tts 0.1.7 requires numpy<2.0.0, but you have numpy 2.4.4
chatterbox-tts 0.1.7 requires safetensors==0.5.3, but you have safetensors 0.8.0
chatterbox-tts 0.1.7 requires transformers==5.2.0, but you have transformers 4.57.1
```

**These are cosmetic — everything works.** Chatterbox's pins are stricter than
what it actually needs, and `gradio` is only used by its standalone web demo.
Do **not** "fix" them: downgrading numpy or transformers breaks Coqui.

### My GPU isn't detected

The startup log prints `GPU True/False`. If it says `False`, reinstall PyTorch
with the index matching your CUDA version:

```bash
pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
```

For the RTX 50XX series, CUDA 12.8 builds are needed instead:

```bash
pip install torch==2.8.0 torchvision==0.23.0 torchaudio==2.8.0 --index-url https://download.pytorch.org/whl/cu128
```

### `coqui-tts[languages]` fails to build

The `[languages]` extra (gruut, mecab, cutlet) is only needed for Japanese and
Chinese, and it often fails to build on Windows. Install the plain package
instead:

```bash
pip install coqui-tts
```

### An engine says "unavailable" in `/health`

The `reason` field tells you which package is missing. Installing only one engine
is perfectly fine: the server routes every request to whatever is available.

---

## Removing the environment

```bash
conda deactivate
conda env list
conda env remove -n local-tts-unified
```

---

## For developers: adding a TTS engine

Engines live in `engines/`, one file each, and are loaded lazily — a missing
Python dependency disables that engine instead of breaking the server.

1. Create `engines/my_engine.py` with a `BaseEngine` subclass implementing
   `available()`, `synthesize(job)` (returns the path of a WAV), `unload_all()`
   and `voices()`. Import heavy libraries **inside** the methods.
2. Register it in `engines/__init__.py` (`ENGINES`), and add its `tts_voice`
   values to `VOICE_ROUTES` if it should own any.

That's it: `/tts` can reach it via `engine: "<id>"`, and `/health` reports it.
