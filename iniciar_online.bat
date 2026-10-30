@echo off
title Sistema HelpDesk TI - Modo Online
echo =========================================================================
echo   INICIANDO SERVIDOR E GERANDO LINK DE ACESSO ONLINE (INTERNET)
echo =========================================================================
echo.
echo 1. Iniciando servidor FastAPI local...
cd /d "%~dp0"
start "Servidor HelpDesk TI (Local)" cmd /k "python -m uvicorn main:app --host 0.0.0.0 --port 8000"

timeout /t 3 >nul

echo 2. Criando link de internet seguro (HTTPS)...
echo.
echo =========================================================================
echo   ATENCAO: Copie o link HTTPS exibido abaixo e envie para seu cliente!
echo   Pressione 'yes' se o Windows perguntar sobre a chave SSH.
echo =========================================================================
echo.

ssh -p 443 -R0:localhost:8000 -o StrictHostKeyChecking=no a.pinggy.io

pause
