@echo off
set "CONDA_ENV=local-tts-unified"

cd /d "%~dp0"

REM Find conda in the usual install locations (same detection as install.bat)
set "CONDA_PATH="
for %%D in (
    "%USERPROFILE%\miniconda3"
    "%USERPROFILE%\anaconda3"
    "%LOCALAPPDATA%\miniconda3"
    "%LOCALAPPDATA%\anaconda3"
    "C:\ProgramData\miniconda3"
    "C:\ProgramData\anaconda3"
    "C:\miniconda3"
    "C:\anaconda3"
) do (
    if not defined CONDA_PATH if exist "%%~D\shell\condabin\conda-hook.ps1" set "CONDA_PATH=%%~D"
)

echo [INFO] Conda's Path : %CONDA_PATH%
echo [INFO] Conda's env : %CONDA_ENV%

if defined CONDA_PATH (
    REM Initialize conda and run all commands automatically
    %WINDIR%\System32\WindowsPowerShell\v1.0\powershell.exe -ExecutionPolicy ByPass -NoExit -Command "& '%CONDA_PATH%\shell\condabin\conda-hook.ps1' ; conda activate '%CONDA_PATH%' ; conda activate %CONDA_ENV% ; uvicorn server_unified:app --host 0.0.0.0 --port 3200"
) else (
    echo [ERROR] Conda has not been found on this machine.
    echo [ERROR] Please run install.bat first ^(it installs Miniconda if needed^).
)
pause
