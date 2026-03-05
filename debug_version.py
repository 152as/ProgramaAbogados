import sys
import os
import openai

print("--- REPORTE DE DIAGNÓSTICO LAI ---")
print(f"1. Ejecutable de Python: {sys.executable}")
print(f"2. Versión de OpenAI detectada: {openai.__version__}")
print(f"3. Ubicación del archivo OpenAI: {os.path.dirname(openai.__file__)}")

try:
    from openai import OpenAI
    client = OpenAI(api_key="sk-test")
    print(f"4. Atributos en client.beta: {dir(client.beta)}")
    
    if hasattr(client.beta, 'vector_stores'):
        print(">>> ESTADO: VECTOR STORES DISPONIBLE ✅")
    else:
        print(">>> ESTADO: VECTOR STORES NO ENCONTRADO ❌ (Versión obsoleta activa)")
except Exception as e:
    print(f"Error al inspeccionar cliente: {e}")

print("------------------------------------")