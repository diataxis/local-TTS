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
    # "cpu1_fr": {
    #     "settings": {
    #         "language":"fr",
    #         "length_scale":1.1,
    #         "noise_scale":0.33,
    #         "noise_w":0.8,
    #     },
    #     "model": "tts_models/multilingual/multi-dataset/your_tts"
    # },
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

vits_langs = {
    "fr": "tts_models/fr/css10/vits",
}
# vits_langs = [
#   {
#     "code": "multilingual",
#     "label": "Multilingual",
#     "models": [
#       "multi-dataset/xtts_v2",
#       "multi-dataset/xtts_v1.1",
#       "multi-dataset/your_tts",
#       "multi-dataset/bark"
#     ]
#   },
#   {
#     "code": "bg",
#     "label": "Bulgarian",
#     "models": ["cv/vits"]
#   },
#   {
#     "code": "cs",
#     "label": "Czech",
#     "models": ["cv/vits"]
#   },
#   {
#     "code": "da",
#     "label": "Danish",
#     "models": ["cv/vits"]
#   },
#   {
#     "code": "et",
#     "label": "Estonian",
#     "models": ["cv/vits"]
#   },
#   {
#     "code": "ga",
#     "label": "Irish",
#     "models": ["cv/vits"]
#   },
#   {
#     "code": "en",
#     "label": "English",
#     "models": [
#       "ek1/tacotron2",
#       "ljspeech/tacotron2-DDC",
#       "ljspeech/tacotron2-DDC_ph",
#       "ljspeech/glow-tts",
#       "ljspeech/speedy-speech",
#       "ljspeech/tacotron2-DCA",
#       "ljspeech/vits",
#       "ljspeech/vits--neon",
#       "ljspeech/fast_pitch",
#       "ljspeech/overflow",
#       "ljspeech/neural_hmm",
#       "vctk/vits",
#       "vctk/fast_pitch",
#       "sam/tacotron-DDC",
#       "blizzard2013/capacitron-t2-c50",
#       "blizzard2013/capacitron-t2-c150_v2",
#       "multi-dataset/tortoise-v2",
#       "jenny/jenny"
#     ]
#   },
#   {
#     "code": "es",
#     "label": "Spanish",
#     "models": [
#       "mai/tacotron2-DDC",
#       "css10/vits"
#     ]
#   },
#   {
#     "code": "fr",
#     "label": "French",
#     "models": [
#       "mai/tacotron2-DDC",
#       "css10/vits"
#     ]
#   },
#   {
#     "code": "uk",
#     "label": "Ukrainian",
#     "models": [
#       "mai/glow-tts",
#       "mai/vits"
#     ]
#   },
#   {
#     "code": "zh-CN",
#     "label": "Chinese (Simplified)",
#     "models": ["baker/tacotron2-DDC-GST"]
#   },
#   {
#     "code": "nl",
#     "label": "Dutch",
#     "models": [
#       "mai/tacotron2-DDC",
#       "css10/vits"
#     ]
#   },
#   {
#     "code": "de",
#     "label": "German",
#     "models": [
#       "thorsten/tacotron2-DCA",
#       "thorsten/vits",
#       "thorsten/tacotron2-DDC",
#       "css10/vits-neon"
#     ]
#   },
#   {
#     "code": "ja",
#     "label": "Japanese",
#     "models": ["kokoro/tacotron2-DDC"]
#   },
#   {
#     "code": "tr",
#     "label": "Turkish",
#     "models": ["common-voice/glow-tts"]
#   },
#   {
#     "code": "it",
#     "label": "Italian",
#     "models": [
#       "mai_female/glow-tts",
#       "mai_female/vits",
#       "mai_male/glow-tts",
#       "mai_male/vits"
#     ]
#   },
#   {
#     "code": "ewe",
#     "label": "Ewe",
#     "models": ["openbible/vits"]
#   },
#   {
#     "code": "hau",
#     "label": "Hausa",
#     "models": ["openbible/vits"]
#   },
#   {
#     "code": "lin",
#     "label": "Lingala",
#     "models": ["openbible/vits"]
#   },
#   {
#     "code": "tw_akuapem",
#     "label": "Twi (Akuapem)",
#     "models": ["openbible/vits"]
#   },
#   {
#     "code": "tw_asante",
#     "label": "Twi (Asante)",
#     "models": ["openbible/vits"]
#   },
#   {
#     "code": "yor",
#     "label": "Yoruba",
#     "models": ["openbible/vits"]
#   },
#   {
#     "code": "hu",
#     "label": "Hungarian",
#     "models": ["css10/vits"]
#   },
#   {
#     "code": "el",
#     "label": "Greek",
#     "models": ["cv/vits"]
#   },
#   {
#     "code": "fi",
#     "label": "Finnish",
#     "models": ["css10/vits"]
#   },
#   {
#     "code": "hr",
#     "label": "Croatian",
#     "models": ["cv/vits"]
#   },
#   {
#     "code": "lt",
#     "label": "Lithuanian",
#     "models": ["cv/vits"]
#   },
#   {
#     "code": "lv",
#     "label": "Latvian",
#     "models": ["cv/vits"]
#   },
#   {
#     "code": "mt",
#     "label": "Maltese",
#     "models": ["cv/vits"]
#   },
#   {
#     "code": "pl",
#     "label": "Polish",
#     "models": ["mai_female/vits"]
#   },
#   {
#     "code": "pt",
#     "label": "Portuguese",
#     "models": ["cv/vits"]
#   },
#   {
#     "code": "ro",
#     "label": "Romanian",
#     "models": ["cv/vits"]
#   },
#   {
#     "code": "sk",
#     "label": "Slovak",
#     "models": ["cv/vits"]
#   },
#   {
#     "code": "sl",
#     "label": "Slovenian",
#     "models": ["cv/vits"]
#   },
#   {
#     "code": "sv",
#     "label": "Swedish",
#     "models": ["cv/vits"]
#   },
#   {
#     "code": "ca",
#     "label": "Catalan",
#     "models": ["custom/vits"]
#   },
#   {
#     "code": "fa",
#     "label": "Persian",
#     "models": [
#       "custom/glow-tts",
#       "custom/vits-female"
#     ]
#   },
#   {
#     "code": "bn",
#     "label": "Bengali",
#     "models": [
#       "custom/vits-male",
#       "custom/vits-female"
#     ]
#   },
#   {
#     "code": "be",
#     "label": "Belarusian",
#     "models": ["common-voice/glow-tts"]
#   }
# ]