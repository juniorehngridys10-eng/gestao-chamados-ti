@echo off
title Sistema de Gestao de Chamados TI - Francisco S Silva
echo =========================================================================
echo   SISTEMA DE GESTAO DE CHAMADOS E SUPORTE EM TI
echo   Contrato: Francisco S Silva Comercio Atacadista & Raimundo Loiola Jr
echo =========================================================================
echo.
echo Iniciando servidor FastAPI na porta 8000...
echo Acesse no seu navegador: http://localhost:8000
echo.

cd /d "%~dp0"
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
