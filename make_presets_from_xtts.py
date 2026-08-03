# Generates Chatterbox reference voices from the xTTSv2 built-in speakers.
#
# It calls a RUNNING TTS server that has the xTTSv2 engine (the legacy
# server.py or server_unified.py, port 3200) and saves each generated sample
# into voices/presets/<Speaker Name>.wav — where Chatterbox picks it up
# immediately (no restart needed).
#
# Usage (with the server running):
#   python make_presets_from_xtts.py "Andrew Chipper" "Damien Black"
#   python make_presets_from_xtts.py --male        # curated masculine list
#   python make_presets_from_xtts.py --female      # curated feminine list
#
# Options:
#   TTS_URL env var to target another server (default http://localhost:3200)
#
# Tip: listen to the results and keep only the good ones (move the rest to
# voices/presets/archived). A clean human recording will always beat a cloned
# synthetic voice — use this for quick volume, not as the gold standard.

import os
import sys
import json
import urllib.request

SERVER = os.environ.get("TTS_URL", "http://localhost:3200")
OUT_DIR = "./voices/presets"

# ~12-15s of continuous, expressive but steady speech — good cloning material.
SAMPLE_TEXT = (
    "Close your eyes and listen carefully to the sound of my voice. "
    "Every word I speak carries its own weight, its own rhythm, and its own intention. "
    "Stay with me, focus on each sentence, and let the story slowly unfold around you, "
    "one breath at a time."
)

# xTTSv2 built-in speakers, split by voice gender
MALE_SPEAKERS = [
    "Andrew Chipper", "Badr Odhiambo", "Dionisio Schuyler", "Royston Min",
    "Viktor Eka", "Abrahan Mack", "Adde Michal", "Baldur Sanjin",
    "Craig Gutsy", "Damien Black", "Gilberto Mathias", "Ilkin Urbano",
    "Kazuhiko Atallah", "Ludvig Milivoj", "Suad Qasim", "Torcull Diarmuid",
    "Viktor Menelaos", "Zacharie Aimilios", "Filip Traverse", "Damjan Chapman",
    "Wulf Carlevaro", "Aaron Dreschner", "Kumar Dahl", "Eugenio Mataracı",
    "Ferran Simen", "Xavier Hayasaka", "Luis Moray", "Marcos Rudaski",
]
FEMALE_SPEAKERS = [
    "Claribel Dervla", "Daisy Studious", "Gracie Wise", "Tammie Ema",
    "Alison Dietlinde", "Ana Florence", "Annmarie Nele", "Asya Anara",
    "Brenda Stern", "Gitta Nikolina", "Henriette Usha", "Sofia Hellen",
    "Tammy Grit", "Tanja Adelina", "Vjollca Johnnie", "Nova Hogarth",
    "Maja Ruoho", "Uta Obando", "Lidiya Szekeres", "Chandra MacFarland",
    "Szofi Granger", "Camilla Holmström", "Lilya Stainthorpe", "Zofija Kendrick",
    "Narelle Moon", "Barbora MacLean", "Alexandra Hisakawa", "Alma María",
    "Rosemary Okafor", "Ige Behringer",
]


def synth(speaker):
    body = json.dumps({
        "text": SAMPLE_TEXT,
        "voice": "speaker",
        "tts_voice": "gpu1",
        "xtts_speaker": speaker,
        "lang": "en",
    }).encode("utf-8")
    req = urllib.request.Request(
        SERVER + "/tts", data=body, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=600) as response:
        wav = response.read()
    path = os.path.join(OUT_DIR, f"{speaker}.wav")
    with open(path, "wb") as f:
        f.write(wav)
    print(f"  saved {path} ({len(wav) // 1024} KB)")


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__ or "Usage: python make_presets_from_xtts.py [--male|--female|SPEAKER...]")
        print("Usage: python make_presets_from_xtts.py --male | --female | \"Speaker Name\"...")
        return

    if args == ["--male"]:
        speakers = MALE_SPEAKERS
    elif args == ["--female"]:
        speakers = FEMALE_SPEAKERS
    else:
        speakers = args

    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Server: {SERVER}")
    print(f"Generating {len(speakers)} preset voice(s) with xTTSv2...")
    failed = []
    for speaker in speakers:
        print(f"- {speaker}")
        try:
            synth(speaker)
        except Exception as err:
            print(f"  FAILED: {err}")
            failed.append(speaker)

    print()
    print(f"Done: {len(speakers) - len(failed)} ok, {len(failed)} failed.")
    if failed:
        print("Failed:", ", ".join(failed))
    print("Listen to the files, keep the good ones, move the rest to voices/presets/archived.")
    print("Then update the ChatterboxSpeakers list in the Eudaimonia client (helpers/TTSFunctions.js).")


if __name__ == "__main__":
    main()
