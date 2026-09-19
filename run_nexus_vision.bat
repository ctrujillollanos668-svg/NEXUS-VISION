@echo off
TITLE NEXUS VISION — Sistema de Camara Inteligente con IA
COLOR 0B

echo ==============================================================================
echo                      NEXUS VISION — SISTEMA DE SEGURIDAD CON IA
echo ==============================================================================
echo.

:: Verificar si el entorno virtual existe
IF NOT EXIST ".venv\Scripts\python.exe" (
    echo [!] Entorno virtual no encontrado. Creando entorno virtual .venv...
    python -m venv .venv
    echo [*] Instalando dependencias requeridas...
    .\.venv\Scripts\pip.exe install -r requirements.txt
)

:: Abrir el navegador automaticamente despues de 2 segundos
echo [*] Iniciando servidor web y centro de control...
start "" cmd /c "timeout /t 2 /nobreak >nul & start http://localhost:8000"

:: Ejecutar la aplicacion principal
.\.venv\Scripts\python.exe main.py

pause
