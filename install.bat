@echo off
setlocal enabledelayedexpansion

REM ===============================================================
REM  Unified TTS server - one-click installer
REM  Just double-click me. I will:
REM    1. find Miniconda/Anaconda (or open the download page if missing)
REM    2. create + activate the 'local-tts-unified' env (python 3.11)
REM    3. detect an NVIDIA GPU to pick the right PyTorch build
REM    4. run installation_unified.bat (all engines, pinned versions)
REM  Everything is installed inside an isolated conda env: your
REM  existing Python installs are never touched.
REM  Optional usage : install.bat [cpu|cu124|cu126]   (default: auto)
REM ===============================================================

set "CONDA_ENV=local-tts-unified"
set PYTHONNOUSERSITE=1
set "VARIANT=%~1"

cd /d "%~dp0"

echo === Step 1/4 : looking for conda ^(Miniconda / Anaconda^) ===
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
    if not defined CONDA_PATH if exist "%%~D\Scripts\activate.bat" set "CONDA_PATH=%%~D"
)
REM Last resort: conda.bat on the PATH (condabin\conda.bat -> root is its parent)
if not defined CONDA_PATH (
    for /f "delims=" %%C in ('where conda.bat 2^>nul') do (
        if not defined CONDA_PATH if exist "%%~dpC..\Scripts\activate.bat" set "CONDA_PATH=%%~dpC.."
    )
)

if not defined CONDA_PATH (
    echo.
    echo [!] Conda was not found on this machine.
    echo     Your browser will now download the Miniconda installer.
    echo.
    echo     1. Run the downloaded installer ^(keep ALL the default options^)
    echo     2. When it is done, double-click this install.bat again
    echo.
    start "" "https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe"
    pause
    exit /b 1
)
echo     Found: %CONDA_PATH%

echo.
echo === Step 2/4 : GPU detection ===
if not "%VARIANT%"=="" goto :variant_done
where nvidia-smi >nul 2>nul
if errorlevel 1 (
    set "VARIANT=cpu"
    echo     No NVIDIA GPU detected - installing the CPU build.
    echo     Kokoro ^(fast^) and VITS will run fine; xTTSv2/Chatterbox will be slow.
) else (
    set "VARIANT=cu124"
    echo     NVIDIA GPU detected - installing the CUDA build ^(cu124^).
)
:variant_done
echo     PyTorch variant: %VARIANT%

echo.
echo === Step 3/4 : conda environment "%CONDA_ENV%" ===
call "%CONDA_PATH%\Scripts\activate.bat" "%CONDA_PATH%"
conda env list | findstr /C:"%CONDA_ENV%" >nul
if errorlevel 1 (
    echo     Creating the environment ^(python 3.11^)...
    call conda create -n %CONDA_ENV% python=3.11 -y || goto :error
)
call conda activate %CONDA_ENV% || goto :error

echo.
echo === Step 4/4 : installing the TTS engines ===
echo     This downloads a few GB and takes 10-20 minutes. Grab a coffee.
echo.
call installation_unified.bat %VARIANT%
if errorlevel 1 goto :error

echo.
echo ============================================================
echo   All done!
echo   Start the server by double-clicking: start_server_unified.bat
echo ============================================================
pause
goto :eof

:error
echo.
echo !!! Installation failed - read the messages above.
echo     You can safely re-run install.bat after fixing the issue.
pause
exit /b 1
