@echo off
echo ===================================================
echo   REPARADOR AUTOMATICO DE LAI SYSTEM (SIMON)
echo ===================================================
echo.
echo 1. Eliminando basura vieja...
if exist venv rmdir /s /q venv

echo.
echo 2. Creando un entorno limpio...
python -m venv venv

echo.
echo 3. Activando entorno...
call venv\Scripts\activate.bat

echo.
echo 4. FORZANDO instalacion de OpenAI moderno...
:: Este comando borra lo que tengas y descarga la version exacta que funciona
pip install --force-reinstall openai==1.55.0
pip install tkinterdnd2 customtkinter Pillow python-dotenv supabase pymupdf

echo.
echo ===================================================
echo   LISTO. YA DEBERIA FUNCIONAR.
echo ===================================================
echo.
echo Iniciando el programa automaticamente...
python main.py
pause