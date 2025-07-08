# local-TTS
Python server with coqui-TTS for eu.daimonia.app
You can find a full guide with videos here: https://eu.daimonia.app/articles/local-TTS
## Getting Started
### 1. Miniconda
Install miniconda from https://www.anaconda.com/download/success

---
## 2. Batch files
Senorgif created two batch files to install and start the Local TTS server on Windows more easily. You can use the two .bat files located at the root of the folder.
```bash
installation.bat
start server.bat
```
You still have to install mini conda before running it.

Make sure to change the following line in the file to the path where Conda is installed on your machine.
```bash
set "CONDA_PATH=[CONDA_PATH]"
```
You can find the path with the following command in conda (line: "base environment")
```bash
conda info
```
---

### 3. Full installation process
If you encounter issues with the batch files, or want to install it manually you can follow these steps.
Open the miniconda terminal and create a virtual environment using `conda` or `venv`.

```bash
conda create -n local-tts python=3.10 -y
conda activate local-tts
```

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
## 3. Runpod Installation Guide
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

---
## 4. Delete the created env and its dependencies
If you want to delete the created environment, you can easily do it by running the following commands in the conda terminal:
```bash
conda remove -n local-tts --all
```