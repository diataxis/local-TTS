@echo off
set "CONDA_PATH=%USERPROFILE%\miniconda3"
set "CONDA_ENV=local-tts"

cd /d "%~dp0"

echo [INFO] Conda's Path : %CONDA_PATH%
echo [INFO] Conda's env : %CONDA_ENV%

if exist "%CONDA_PATH%\shell\condabin\conda-hook.ps1" (
    REM To create environment first time
    %WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe -ExecutionPolicy ByPass -NoExit -Command "& '%CONDA_PATH%\shell\condabin\conda-hook.ps1' ; conda activate '%CONDA_PATH%' ; conda create -n %CONDA_ENV% python=3.10 -y ; conda activate local-tts ; pip install -r requirements.txt ; uvicorn server:app --host 0.0.0.0 --port 3200"
) else (
    echo [ERROR] Conda has not been found in %CONDA_PATH%
    echo [ERROR] Please install Miniconda or change the CONDA_PATH.
)
pause