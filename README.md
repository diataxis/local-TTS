# local-TTS
Python server with coqui-TTS for eu.daimonia.app

## Getting Started
### 1. Set Up Environment

Create a virtual environment using `conda` or `venv`.

```bash
conda create -n local-tts python=3.10 -y
conda activate local-tts
```

### 2. Install Requirements
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```
```bash
pip install -r requirements.txt
```
### 3. Start the Server

```bash
uvicorn server:app --host 0.0.0.0 --port 3200
```

This starts a FastAPI server on `http://localhost:3200/tts`.

---