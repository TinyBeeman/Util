if not defined PYTHON (set PYTHON=python)

pip install regex
pip install Pillow

:launch
REM This pattern matches this anystring-anystring-token,anystring-anystring
%PYTHON% get_sd_info_from_png.py --image %1
pause
exit /b

:show_stdout_stderr
echo.
echo exit code: %errorlevel%
pause
exit /b
