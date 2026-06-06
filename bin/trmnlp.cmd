@echo off
REM Windows wrapper mirroring bin/trmnlp: run trmnlp locally if installed,
REM otherwise via Docker. Usage from the repo root, e.g.:  bin\trmnlp serve

where trmnlp >nul 2>nul
if %ERRORLEVEL%==0 (
    trmnlp %*
    exit /b %ERRORLEVEL%
)

REM Determine XDG config dir on host (where `trmnlp login` saves the API key)
if defined XDG_CONFIG_HOME (
    set "CONFIG_DIR=%XDG_CONFIG_HOME%\trmnlp"
) else (
    set "CONFIG_DIR=%USERPROFILE%\.config\trmnlp"
)
if not exist "%CONFIG_DIR%" mkdir "%CONFIG_DIR%"

where docker >nul 2>nul
if %ERRORLEVEL%==0 (
    docker run -it --rm ^
        --publish 4567:4567 ^
        --volume "%CD%:/plugin" ^
        --volume "%CONFIG_DIR%:/root/.config/trmnlp" ^
        trmnl/trmnlp %*
    exit /b %ERRORLEVEL%
)

echo Install Docker Desktop: https://docs.docker.com/get-docker/
exit /b 1
