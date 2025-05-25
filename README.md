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
You may have to install espeak-ng, goto : https://github.com/espeak-ng/espeak-ng/blob/master/docs/guide.md and follow the installation instructions.
Restart your computer.
For Nvidia GPU (Cuda 11.8, replace with your version):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```
For CPU (Cuda 11.8, replace with your version):
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
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