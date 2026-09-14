@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ===============================================
echo   Threads Prospecting - Inicializador
echo ===============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Python nao foi encontrado no PATH.
    echo Instale o Python 3.10+ em https://www.python.org/downloads/
    echo e marque a opcao "Add Python to PATH" durante a instalacao.
    echo.
    pause
    exit /b 1
)

if not exist ".venv" (
    echo Criando ambiente virtual em .venv ...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERRO] Falha ao criar o ambiente virtual.
        pause
        exit /b 1
    )
)

call ".venv\Scripts\activate.bat"

echo Instalando dependencias ^(pode levar um instante^)...
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo [ERRO] Falha ao instalar as dependencias.
    pause
    exit /b 1
)

if not exist ".env" (
    echo.
    echo Criando .env a partir do modelo...
    copy /y ".env.example" ".env" >nul
    echo Abra o Bloco de Notas e preencha sua ANTHROPIC_API_KEY.
    notepad ".env"
)

if not exist "account.yaml" (
    echo.
    echo Criando account.yaml a partir do modelo...
    copy /y "account.example.yaml" "account.yaml" >nul
    echo Abra o Bloco de Notas e preencha nicho, tom, publico e nome_da_conta.
    notepad "account.yaml"
)

:menu
echo.
echo ===============================================
echo   O que voce quer fazer?
echo     1 - Gerar um novo post
echo     2 - Gerar uma resposta a um comentario
echo     3 - Sair
echo ===============================================
set "opcao="
set /p opcao="Escolha uma opcao (1-3): "

if "%opcao%"=="1" goto post
if "%opcao%"=="2" goto reply
if "%opcao%"=="3" goto fim
echo Opcao invalida, tente novamente.
goto menu

:post
echo.
set "topico="
set /p topico="Tema/assunto do post: "
if "%topico%"=="" (
    echo Voce precisa digitar um tema.
    goto menu
)
python -m threads_prospecting.cli post --topic "%topico%"
echo.
pause
goto menu

:reply
echo.
set "comentario="
set /p comentario="Cole o comentario que deseja responder: "
if "%comentario%"=="" (
    echo Voce precisa colar um comentario.
    goto menu
)
python -m threads_prospecting.cli reply --comment "%comentario%"
echo.
pause
goto menu

:fim
echo.
echo Ate mais!
pause
exit /b 0
