import os
# os.environ["PATH"] = r"C:\Program Files\eSpeak NG;" + os.environ["PATH"]
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import uuid
from TTS.api import TTS
from pydub import AudioSegment
app = FastAPI()
import torch
from presets import *

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
print("GPU", torch.cuda.is_available())
print("GPU", torch.cuda.get_device_name(torch.cuda.current_device()))

device = "cuda" if torch.cuda.is_available() else "cpu"
# Load the model and set voices
# tts_models/en/vctk/vits
# tts_models/en/ljspeech/tacotron2-DDC : no speaker
# tts_models/en/jenny/jenny : no speaker
# tts_models/multilingual/multi-dataset/xtts_v2
# tts_model = TTS(model_name="tts_models/en/jenny/jenny", progress_bar=False).to(device)
# tts_model = TTS(model_name="tts_models/en/vctk/vits", progress_bar=False).to(device)
# tts_model = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False).to(device)

# preset = presets[data.get("preset")]
tts_model = False
current_model = ""
default_speaker_voice = "p294"
default_narrator_voice = "p248"

@app.post("/tts")
async def generate_tts(request: Request):
    global tts_model
    global current_model
    data = await request.json()
    text = data.get("text", "").strip()
    role = data.get("voice", "speaker")  # "speaker" or "narrator"
    tts_voice = data.get("tts_voice")
    print("tts_voice", tts_voice)
    preset = presets[tts_voice]
    if tts_model == False or preset['model'] != current_model:
        tts_model = TTS(model_name=preset['model'], progress_bar=True).to(device)
        current_model = preset['model']
        
    if not text:
        return {"error": "No text provided"}

    # Select voice and prosody based on role
    if role == "narrator":
        speaker = default_narrator_voice
        length_scale = 1.2
        noise_scale = 0.2
        noise_w = 0.6
    else:
        speaker = default_speaker_voice
        length_scale = 1.1
        noise_scale = 0.33
        noise_w = 0.8

    tmp_wav = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.wav")
    print('path', tmp_wav)
    tmp_mp3 = tmp_wav.replace(".wav", ".mp3")

    # tts_model.tts_to_file(
    #     text=text,
    #     # speaker=speaker,
    #     file_path=tmp_wav,
        
    #     # length_scale=length_scale,
    #     # noise_scale=noise_scale,
    #     # noise_w=noise_w,
        
    #     language="en",
    #     speaker_wav=["./voices/nicole.wav"]
    # )
    preset['settings']['text'] = text
    preset['settings']['file_path'] = tmp_wav
    tts_model.tts_to_file(
        **preset['settings']
    )
    audio = AudioSegment.from_wav(tmp_wav)
    audio.export(tmp_mp3, format="mp3")
    os.remove(tmp_wav)

    return FileResponse(tmp_mp3, media_type="audio/mpeg", filename="speech.mp3")
