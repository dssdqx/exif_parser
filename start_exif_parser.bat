@echo off
set "SCRIPT_DIR=%~dp0"
set "PATH=%SCRIPT_DIR%;%PATH%"
python "%SCRIPT_DIR%main.py" %*
@pause