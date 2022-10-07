if not defined PYTHON (set PYTHON=python)

pip install regex

:launch
REM This pattern matches this anystring-anystring-token,anystring-anystring
%PYTHON% D:\Apps\util\Util\Python\sort_files.py --v --pattern "(?:[^_]+_){2}p\((?P<token>[^_\|]+)"
pause
exit /b

:show_stdout_stderr
echo.
echo exit code: %errorlevel%
pause
exit /b
