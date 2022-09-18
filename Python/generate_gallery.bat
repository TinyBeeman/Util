if not defined PYTHON (set PYTHON=python)

:launch
REM This pattern matches this anystring-anystring-token,anystring-anystring
%PYTHON% generate_gallery.py
pause
exit /b

:show_stdout_stderr
echo.
echo exit code: %errorlevel%
pause
exit /b
