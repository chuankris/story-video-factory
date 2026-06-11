@echo off
REM Smoke test for comic-video-composer: builds a fake 3-segment episode
REM with ffmpeg-generated images/audio, then runs compose.py.
REM Requires: python + ffmpeg on PATH. Run from repo root:
REM   tests\smoke_compose.bat

setlocal
set EP=tests\fixture-episode
if exist %EP% rmdir /s /q %EP%
mkdir %EP%\assets\images %EP%\assets\audio

REM script.json (3 segments)
> %EP%\script.json (
echo {"episode":"测试","title_working":"smoke","segments":[
echo {"id":1,"role":"narration","text":"一个大活人，睡到半夜，床底下伸出一只手来。","beat":"hook","panel_hint":"床底伸手"},
echo {"id":2,"role":"narration","text":"列位看官，这事就出在徽州程家。","beat":"setup","panel_hint":"徽州街景"},
echo {"id":3,"role":"narration","text":"你道这只手，到底是人是鬼？","beat":"close","panel_hint":"特写"}
echo ]}
)

REM fake panels (colored frames with text-free gradients)
ffmpeg -y -f lavfi -i color=c=0x334455:s=1080x1440 -frames:v 1 %EP%\assets\images\1.png
ffmpeg -y -f lavfi -i color=c=0x553344:s=1080x1440 -frames:v 1 %EP%\assets\images\2.png
ffmpeg -y -f lavfi -i color=c=0x445533:s=1080x1440 -frames:v 1 %EP%\assets\images\3.png

REM fake narration (2-3s sine beeps)
ffmpeg -y -f lavfi -i "sine=frequency=440:duration=2.5" -c:a libmp3lame %EP%\assets\audio\1.mp3
ffmpeg -y -f lavfi -i "sine=frequency=550:duration=2.0" -c:a libmp3lame %EP%\assets\audio\2.mp3
ffmpeg -y -f lavfi -i "sine=frequency=660:duration=3.0" -c:a libmp3lame %EP%\assets\audio\3.mp3

REM compose
python skills\comic-video-composer\scripts\compose.py --episode %EP%
if errorlevel 1 (
  echo SMOKE TEST FAILED
  exit /b 1
)

echo.
echo SMOKE TEST PASSED. Check %EP%\output\draft.mp4
echo Expect: ~8s, 9:16, 3 color blocks with zoom/pan, subtitles, beeps.
endlocal
