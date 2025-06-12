# local-TTS
Python server with coqui-TTS for eu.daimonia.app
You can find a full guide with videos here: https://eu.daimonia.app/articles/local-TTS
## Getting Started
### 1. Set Up Environment

Create a virtual environment using `conda` or `venv`.

```bash
conda create -n local-tts python=3.10 -y
conda activate local-tts
```

### 2. Install Requirements
You may have to install espeak-ng, goto : https://github.com/espeak-ng/espeak-ng/blob/master/docs/guide.md and follow the installation instructions.
Restart your computer.

```bash
pip install -r requirements.txt
```
If your GPU is not detected or have a torch error, installing the following dependencies can solve the issue.
For Nvidia GPU (replace cu118 with you CUDA version if needed):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```
For CPU:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

### 3. Start the Server

```bash
uvicorn server:app --host 0.0.0.0 --port 3200
```

This starts a FastAPI server on `http://localhost:3200/tts`.

---
### 3. Runpod Installation Guide
```bash
apt update
```
```bash
apt-get install espeak-ng
```
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```
```bash
git clone https://github.com/diataxis/local-TTS.git
```
```bash
cd local-TTS/
```
```bash
pip install -r requirements.txt
```
```bash
uvicorn server:app --host 0.0.0.0 --port 3200
```