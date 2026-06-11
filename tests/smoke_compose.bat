@echo off
REM ASCII-only wrapper. cmd parses .bat files in the system codepage (GBK on
REM Chinese Windows), so JSON/Chinese must never live inside a .bat file.
REM All real logic is in the Python script:
python "%~dp0smoke_compose.py"
