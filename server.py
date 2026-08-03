import os
# os.environ["PATH"] = r"C:\Program Files\eSpeak NG;" + os.environ["PATH"]
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import uuid
from TTS.api import TTS
# from pydub import AudioSegment
import torch
from presets import *
import shutil

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.middleware("http")
async def add_custom_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response

print("GPU", torch.cuda.is_available())
print("CUDA Version", torch.version.cuda)
if (torch.cuda.is_available()):
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
default_lang = "en"

@app.post("/tts")
async def generate_tts(request: Request):
    global tts_model
    global current_model
    data = await request.json()
    text = data.get("text", "").strip()
    role = data.get("voice", "speaker")  # "speaker" or "narrator"
    lang = data.get("lang", "en") if data.get("text") != None else default_lang
    xtts_speaker = data.get("xtts_speaker")
    tts_voice = data.get("tts_voice")
    print("tts_voice", tts_voice)
    print("xtts_speaker", xtts_speaker)
    preset = presets[tts_voice]
    word_count = len(text.split())
    if tts_model == False or preset['model'] != current_model:
        tts_model = TTS(model_name=preset['model'], progress_bar=True).to(device)
        current_model = preset['model']

    print("current_model", current_model)

    if not text:
        return {"error": "No text provided"}

    # Select voice and prosody based on role
    # if role == "narrator":
    #     speaker = default_narrator_voice
    #     length_scale = 1.2
    #     noise_scale = 0.2
    #     noise_w = 0.6
    # else:
    #     speaker = default_speaker_voice
    #     length_scale = 1.1
    #     noise_scale = 0.33
    #     noise_w = 0.8

    tmp_wav = os.path.join(tempfile.gettempdir(), f"{uuid.uuid4()}.wav")
    print('path', tmp_wav)

    if tts_voice == "gpu1" and xtts_speaker == "nicole":
        preset['settings']["speaker"] = None
        preset['settings']["speaker_wav"] = ["./voices/nicole.wav"]
        
    elif tts_voice == "cloning":
        preset['settings']["speaker"] = None
        preset['settings']["speaker_wav"] = ["./voices/my_voices/" + xtts_speaker]
        
    elif xtts_speaker is not None and xtts_speaker != "nicole":
        preset['settings']["speaker"] = xtts_speaker
        preset['settings']["speaker_wav"] = None
    
    if tts_voice == "gpu1" or tts_voice == "cloning":
        print('Language set to :', lang)
        preset['settings']["language"] = lang

    preset['settings']['text'] = text
    preset['settings']['file_path'] = tmp_wav
    
    preset['settings']['split_sentences'] = True
    if word_count <= 3 and tts_voice in ("gpu1", "cloning"):
        print("Short text detected, disabling sentence splitting, adding noise")
        # text = f"Well, {text}"
        preset['settings']['split_sentences'] = False
    
    
    print('preset', preset)
    tts_model.tts_to_file(
        **preset['settings'],
        temperature=0.7,
        top_p=0.85,
    )

    return FileResponse(tmp_wav, media_type="audio/mpeg", filename="speech.mp3")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    print(file.filename)
    file_location = f"{'./voices/my_voices/'}/{file.filename}"
    
    # Enregistrement du fichier
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return JSONResponse(content={"filename": file.filename, "success": True})
