@echo off
setlocal enabledelayedexpansion

REM ===============================================================
REM  Unified TTS server - Windows installation script
REM  Installe Coqui (xTTSv2 + VITS) ET Chatterbox dans le meme env.
REM  Prerequis : conda create -n local-tts-unified python=3.11 -y
REM              conda activate local-tts-unified
REM  Usage : installation_unified.bat [cpu|cu124|cu126]   (defaut: cu124)
REM ===============================================================

set PYTHONNOUSERSITE=1
set "VARIANT=%~1"
if "%VARIANT%"=="" set "VARIANT=cu124"

echo === Verification de l'environnement Python actif ===
python -c "import sys; print('Python exe :', sys.executable)"
python -c "import sys; assert 'local-tts-unified' in sys.executable.lower(), 'ERREUR : l''env local-tts-unified n''est pas actif !'"
if errorlevel 1 (
    echo.
    echo !!! L'env conda 'local-tts-unified' n'est pas actif. Lance 'conda activate local-tts-unified' d'abord.
    exit /b 1
)

echo.
echo === Variante PyTorch selectionnee : %VARIANT% ===

echo.
echo === Mise a jour de pip / setuptools / wheel ===
python -m pip install --upgrade pip setuptools wheel || goto :error

echo.
echo === Installation de PyTorch (%VARIANT%) ===
if /I "%VARIANT%"=="cpu" (
    python -m pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu || goto :error
) else if /I "%VARIANT%"=="cu124" (
    python -m pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124 || goto :error
) else if /I "%VARIANT%"=="cu126" (
    python -m pip install torch==2.6.0 torchvision==0.21.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu126 || goto :error
)

echo.
echo === Installation de Coqui TTS (xTTSv2 + VITS) ===
REM Le pack [languages] (gruut, mecab, cutlet...) compile mal sous Windows et
REM ne sert QUE au japonais/chinois : on retombe sur coqui-tts nu si ca echoue.
python -m pip install "coqui-tts[languages]"
if errorlevel 1 (
    echo.
    echo [WARN] coqui-tts[languages] a echoue - nouvelle tentative sans les langues ^(ja/zh indisponibles^)
    python -m pip install coqui-tts || goto :error
)

echo.
echo === Installation des dependances Chatterbox ===
python -m pip install diffusers==0.29.0 ^
  conformer==0.3.2 resemble-perth==1.0.1 ^
  librosa==0.11.0 pykakasi==2.3.0 || goto :error

echo.
echo === Installation de s3tokenizer ===
python -m pip install onnx==1.16.2 || goto :error
python -m pip install --no-deps s3tokenizer==0.2.0 || goto :error

echo.
echo === Installation de chatterbox-tts (sans deps pour proteger torch/transformers) ===
python -m pip install --no-deps chatterbox-tts || goto :error

echo.
echo === Installation de pyloudnorm + omegaconf ===
python -m pip install pyloudnorm omegaconf || goto :error

echo.
echo === Installation des dependances FastAPI ===
python -m pip install fastapi==0.110.1 uvicorn==0.29.0 python-multipart==0.0.9 pydub==0.25.1 || goto :error

echo.
echo === Installation de Kokoro-82M (mode "fast", optionnel) ===
REM Deps non-epinglees : conserve le torch/transformers deja installes.
REM espeakng-loader (via misaki[en]) embarque le binaire espeak-ng, rien a installer.
python -m pip install kokoro==0.9.4 soundfile
if errorlevel 1 (
    echo [WARN] kokoro a echoue - le serveur fonctionnera sans le mode "fast"
)

echo.
echo === Arbitrage transformers (LE point critique) ===
REM coqui-tts declare transformers>=4.57 mais son code importe isin_mps_friendly,
REM supprime dans transformers 5.x -> coqui casse avec une 5.x.
REM chatterbox-tts epingle ==5.2.0 mais tourne parfaitement en 4.57.1 (teste).
REM 4.57.1 est donc la seule version qui contente les deux : on la force EN DERNIER.
REM Les warnings pip de chatterbox (gradio/numpy/safetensors/transformers) sont
REM COSMETIQUES : ses pins sont trop stricts, tout fonctionne. Ne pas y toucher.
python -m pip install transformers==4.57.1 || goto :error

echo.
echo === Verification finale ===
python -c "import torch; print('torch', torch.__version__, '| CUDA:', torch.cuda.is_available())" || goto :error
python -c "import TTS.api; print('coqui-tts OK')" || goto :error
python -c "import chatterbox; print('chatterbox OK')" || goto :error
python -c "import kokoro; print('kokoro OK')" || echo [WARN] kokoro absent (mode "fast" indisponible)
python -c "import fastapi, uvicorn; print('fastapi OK')" || goto :error

echo.
echo ============================================================
echo   Installation terminee avec succes !
echo   Lance le serveur avec :
echo     python -m uvicorn server_unified:app --host 0.0.0.0 --port 3200
echo ============================================================
goto :eof

:error
echo.
echo !!! ERREUR pendant l'installation - voir les messages ci-dessus.
exit /b 1
