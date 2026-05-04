@echo off
setlocal EnableExtensions

rem Customer launcher. In the packaged version it starts the bundled EXE.
rem In a source checkout it falls back to Python for developer smoke tests.

set "APP_ROOT=%~dp0"
set "APP_EXE=%APP_ROOT%CatalogLocalizer.exe"

if exist "%APP_EXE%" (
  if "%~1"=="" (
    start "" "%APP_EXE%"
    exit /b 0
  )
  "%APP_EXE%" %*
  exit /b %ERRORLEVEL%
)

if exist "%APP_ROOT%src\russian_catalog_localizer\desktop_app.py" goto :found_source
if exist "%APP_ROOT%..\src\russian_catalog_localizer\desktop_app.py" (
  for %%I in ("%APP_ROOT%..") do set "APP_ROOT=%%~fI\"
  goto :found_source
)

echo [ERROR] Cannot find the bundled application.
echo Please keep this launcher next to CatalogLocalizer.exe.
pause
exit /b 1

:found_source
set "PYTHON_EXE="
where py >nul 2>nul
if not errorlevel 1 set "PYTHON_EXE=py -3"

if not defined PYTHON_EXE (
  where python >nul 2>nul
  if not errorlevel 1 set "PYTHON_EXE=python"
)

if not defined PYTHON_EXE (
  echo [ERROR] Python 3.11 or newer was not found for source-mode fallback.
  pause
  exit /b 1
)

set "PYTHONPATH=%APP_ROOT%src;%PYTHONPATH%"
pushd "%APP_ROOT%" >nul
if errorlevel 1 (
  echo [ERROR] Cannot enter package folder: %APP_ROOT%
  pause
  exit /b 1
)

if "%~1"=="" (
  %PYTHON_EXE% -m russian_catalog_localizer
) else (
  %PYTHON_EXE% -m russian_catalog_localizer %*
)
set "EXIT_CODE=%ERRORLEVEL%"
popd >nul

if not "%EXIT_CODE%"=="0" (
  echo.
  echo [ERROR] The application exited with code %EXIT_CODE%.
  pause
  exit /b %EXIT_CODE%
)

exit /b 0
