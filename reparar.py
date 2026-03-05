import sys
import subprocess
import os
import importlib

print("--------------------------------------------------")
print(f"🔍 DIAGNÓSTICO: Usando Python en: {sys.executable}")

def forzar_instalacion():
    print("🧹 1. Eliminando versión vieja de OpenAI...")
    subprocess.check_call([sys.executable, "-m", "pip", "uninstall", "-y", "openai"])
    
    print("⬇️ 2. Descargando OpenAI versión moderna...")
    # Forzamos una versión que sabemos que funciona (1.55.0 o superior)
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openai>=1.55.0"])

try:
    import openai
    print(f"⚠️ Versión actual detectada antes de arreglar: {openai.__version__}")
except ImportError:
    print("⚠️ OpenAI no estaba instalado.")

# EJECUTAR LA REPARACIÓN
forzar_instalacion()

print("--------------------------------------------------")
print("✅ REPARACIÓN COMPLETADA.")
print("Por favor, cierra esta ventana y ejecuta 'python main.py' ahora.")
print("--------------------------------------------------")