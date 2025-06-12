presets = {
    "cpu1": {
        "settings": {
            "speaker":"p294",
            "length_scale":1.1,
            "noise_scale":0.33,
            "noise_w":0.8,
        },
        "model": "tts_models/en/vctk/vits"
    },
    "gpu1": {
        "settings": {
            "language":"en",
            "speaker_wav":["./voices/nicole.wav"]
        },
        "model": "tts_models/multilingual/multi-dataset/xtts_v2"
    },
    "cloning": {
        "settings": {
            "language":"en",
            "speaker_wav":["./voices/nicole.wav"]
        },
        "model": "tts_models/multilingual/multi-dataset/xtts_v2"
    }
}
