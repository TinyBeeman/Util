if not defined PYTHON (set PYTHON=python)

pip install regex

:launch
REM This pattern matches this anystring-anystring-token,anystring-anystring
%PYTHON% sort_files.py --v --pattern "(?:[^-]+-){2}(?P<token>[^-,]+)"
pause
exit /b

:show_stdout_stderr
echo.
echo exit code: %errorlevel%
pause
exit /b
