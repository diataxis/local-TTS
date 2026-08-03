# Unified local TTS server

One server that hosts **all** the local TTS engines behind the same API as the
two legacy servers (`server.py` here, and the separate `local-tts-chatterbox`
repo). Existing Eudaimonia frontends work without any change.

- **Coqui** — VITS (`cpu1`) and xTTSv2 (`gpu1`, `cloning`)
- **Chatterbox** — turbo / standard / multilingual sub-models, voice cloning
- **Kokoro-82M** — `fast` mode: ~15× real time on GPU, <1GB VRAM, 54 fixed
  voices (no cloning), 9 languages
- Extensible: a new technology = one new file in `engines/`

The legacy `server.py` is untouched and still works exactly as before.

## Files

```
server_unified.py            # FastAPI app: /tts /upload /voices /health
engines/
    __init__.py              # registry + routing + VRAM exclusivity
    base.py                  # BaseEngine interface
    coqui_engine.py          # port of the legacy server.py
    chatterbox_engine.py     # port of local-tts-chatterbox/server.py
    kokoro_engine.py         # Kokoro-82M "fast" mode
voices/
    nicole.wav               # default reference voice
    presets/                 # Chatterbox reference WAVs (xTTS speaker names)
    my_voices/               # user uploads (/upload) — shared by all engines
installation_unified.bat     # Windows install (both stacks in one conda env)
start_server_unified.bat     # Windows start script
```

## Install (Windows)

```bash
conda create -n local-tts-unified python=3.11 -y
conda activate local-tts-unified
installation_unified.bat cu124        # or cpu / cu126
```

espeak-ng is still required for VITS (`cpu1`), same as the legacy server.

## Run

```bash
uvicorn server_unified:app --host 0.0.0.0 --port 3200
```

or double-click `start_server_unified.bat`.

## API

### `POST /tts` → WAV

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
| `tts_voice` | `cpu1` (VITS), `gpu1` (xTTSv2), `cloning` (uploaded voice), `standard` (Chatterbox), `turbo` (Chatterbox turbo), `fast` (Kokoro) |
| `xtts_speaker` | Speaker name (xTTS/VITS), preset name, uploaded filename, or Kokoro voice (`af_heart`, `af_bella`, `am_michael`...) |
| `lang` | Language code. Non-English on Chatterbox auto-switches to its multilingual model |
| `engine` | *(optional)* Force an engine: `coqui`, `chatterbox` or `kokoro`. Overrides the `tts_voice` routing |
| `exaggeration` / `cfg_weight` | *(optional, Chatterbox standard/multilingual)* 0.0–1.0 |
| `speed` | *(optional, Kokoro)* speech rate, default 1.0 |

**Routing**: `cpu1`/`gpu1`/`cloning` → Coqui, `standard`/`turbo` → Chatterbox,
`fast` → Kokoro.
If the routed engine's Python dependencies are missing, the request **falls
back** to whichever engine is installed — so a Chatterbox-only install keeps
serving `gpu1`/`cloning` (like the legacy chatterbox server did), and a
Coqui-only install answers `standard` with xTTSv2.

**Chatterbox voice cloning**: send `engine: "chatterbox"` with
`tts_voice: "cloning"` and `xtts_speaker: "<uploaded file>"`. (Also works
implicitly: `standard` + an uploaded filename resolves to `my_voices/`.)

**Narrator**: nothing engine-specific server-side — a narrator line is just a
request with a different `xtts_speaker`. Works with every engine, including
Chatterbox (pick any preset/uploaded voice as the narrator voice).

### `POST /upload`

Multipart file upload → saved in `voices/my_voices/` (shared by all engines)
→ `{ "filename": "...", "success": true }`.

### `GET /voices`

Catalog: legacy keys (`presets`, `my_voices`, `default`) + per-engine voices
and availability. Lets a frontend build its pickers dynamically instead of
hardcoding voice lists.

### `GET /health`

Engine availability (with the reason when a lib is missing) and currently
loaded models. Lets a frontend grey out unavailable modes.

## Memory management

Both heavy stacks target ~4GB VRAM GPUs and generally can't coexist, so by
default synthesizing with one engine **unloads the others first**
(`TTS_EXCLUSIVE=false` to disable). Within Chatterbox, the sub-model LRU of the
legacy server is kept (`CHATTERBOX_MAX_MODELS`, default 1).

Kokoro is **lightweight** (<1GB VRAM) and exempt from this exclusivity: a
`fast` request never evicts xTTSv2/Chatterbox, and they never evict Kokoro.

## Environment variables

| Var | Effect |
|---|---|
| `TTS_DEVICE` | Force device for every engine (`cuda`, `cpu`, `mps`) |
| `TTS_EXCLUSIVE` | `false` = let several engines stay loaded together (default `true`) |
| `TTS_PRELOAD` | Models to load at startup, e.g. `chatterbox:turbo` or `coqui:gpu1` (default: none, lazy) |
| `CHATTERBOX_DEVICE` | Chatterbox-only device override (legacy name, still honored) |
| `KOKORO_DEVICE` | Kokoro-only device override |
| `CHATTERBOX_MAX_MODELS` | Chatterbox sub-model LRU size (default 1) |
| `CHATTERBOX_VOICE_CACHE` | Voice embedding cache size (default 16) |
| `CHATTERBOX_DTYPE` | `float16` for half precision (experimental) |
| `CHATTERBOX_COMPILE` | `true` to torch.compile the T3 transformer |

## Conflits de dépendances — RÉSOLU (testé 2026-07-30)

Un seul env conda suffit : **coqui-tts 0.27.5 + chatterbox-tts 0.1.7 cohabitent
avec `transformers==4.57.1`**, torch 2.6.0+cu124, numpy 2.4.4, Python 3.11.

Le point unique de friction est `transformers` :

- `coqui-tts` **déclare** `transformers>=4.57`, mais son code importe
  `isin_mps_friendly` depuis `transformers.pytorch_utils`, **supprimé en 5.x**.
  Donc coqui casse avec toute version 5.x (`ImportError: cannot import name
  'isin_mps_friendly'`) — sa borne haute manque, c'est un bug amont.
- `chatterbox-tts` **épingle** `transformers==5.2.0`, mais fonctionne en réalité
  très bien en 4.57.1 (les 3 modèles standard/turbo/multilingual importent).

`4.57.1` est donc la seule fenêtre qui contente les deux, et les scripts
d'installation la forcent **en dernier**, après tout le reste, pour que rien ne
la remonte.

**Les avertissements pip de chatterbox sont cosmétiques** — ses pins sont trop
stricts, tout marche :

```
chatterbox-tts 0.1.7 requires gradio==6.8.0, which is not installed.
chatterbox-tts 0.1.7 requires numpy<2.0.0, but you have numpy 2.4.4
chatterbox-tts 0.1.7 requires safetensors==0.5.3, but you have safetensors 0.8.0
chatterbox-tts 0.1.7 requires transformers==5.2.0, but you have transformers 4.57.1
```

`gradio` n'est utilisé que par la démo web de chatterbox (inutile ici).
**Ne pas "corriger" ces warnings** : downgrader numpy ou transformers casserait
coqui.

En cas de régression future (nouvelle version d'un des deux paquets), le repli
reste possible sans rien réécrire : le serveur unifié démarre même avec un seul
moteur importable, le détecte et route vers ce qui marche (`GET /health`), donc
deux envs conda + deux serveurs restent une option.

## Recréer l'env conda from scratch

```bash
conda env list
conda deactivate
conda env remove -n local-tts-unified
```

Puis relancer `install_unified_perso.bat` (il recrée l'env s'il n'existe pas).

## Voix de référence Chatterbox

Chatterbox ne fait **que du clonage** : chaque "voix" est un WAV de référence
dans `voices/presets/`. Le sous-dossier `archived/` est ignoré par le serveur
(`GET /voices` ne liste que la racine de `presets/`), c'est le bon endroit pour
mettre de côté les voix ratées.

Un bon échantillon : **7 à 20 s**, une seule personne, débit régulier, pas de
musique/bruit/réverbération, pas de blancs longs, mono, 24 kHz ou plus, WAV
16-bit, sans compression agressive ni normalisation brutale. Le nom du fichier
est le nom affiché côté client.

Pour fabriquer des voix rapidement à partir des 58 speakers intégrés d'xTTSv2
(le serveur doit tourner avec le moteur xTTSv2 disponible) :

```bash
python make_presets_from_xtts.py --male
python make_presets_from_xtts.py --female
python make_presets_from_xtts.py "Damien Black" "Craig Gutsy"
```

Les WAV sont écrits dans `voices/presets/` et pris en compte **immédiatement**
(pas de redémarrage). Écouter, garder les bons, déplacer les autres dans
`voices/presets/archived/`.

## Adding a new engine

1. Create `engines/my_engine.py` with a `BaseEngine` subclass:
   `available()`, `synthesize(job) -> wav path`, `unload_all()`, `voices()`.
   Import the heavy libraries **inside the methods** (lazy).
2. Register it in `engines/__init__.py` (`ENGINES`) and, if it should own
   some `tts_voice` values, add them to `VOICE_ROUTES`.
3. Done — `/tts` can reach it via `engine: "<id>"`, `/health` reports it.
