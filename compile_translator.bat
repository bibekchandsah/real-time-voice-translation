@echo off
title Real-time Voice Translator - Smart Compilation Tool
echo.
echo =============================================
echo   Real-time Voice Translator Compiler
echo =============================================
echo.
echo This script will let you choose between:
echo.
echo 1. OPTIMIZED BUILD (45MB, 3 min) - Recommended
echo    - Fast compilation and small size
echo    - All core translation features
echo.
echo 2. FULL BUILD (690MB, 15-20 min)
echo    - Complete with all dependencies
echo    - Longer compilation time
echo.
echo Custom icon support: Place icon.ico or icon.png in this folder
echo.
pause

python compile_optimized.py
pause