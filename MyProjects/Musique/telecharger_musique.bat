@echo off
set URL=%1
set OUTDIR=%2

:: Vérifie que yt-dlp est installé
where yt-dlp >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ yt-dlp n'est pas installé ou pas dans le PATH.
    exit /b 1
)

:: Télécharger l'audio en MP3
yt-dlp -f bestaudio --extract-audio --audio-format mp3 --audio-quality 0 ^
-o "%OUTDIR%\%%(title)s.%%(ext)s" ^
--ffmpeg-location "path" %URL%
pause
