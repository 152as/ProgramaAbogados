import os
from openai import OpenAI
from dotenv import load_dotenv

# Cargar claves
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- LISTA MAESTRA DE LEYES (Asegúrate de tenerlos en la carpeta) ---
archivos_legales = [
    "constitucion_panama.pdf",
    "reglamento_transito.pdf",
    "codigo_trabajo.pdf",
    "codigo_familia.pdf",
    "codigo_penal.pdf",
    "codigo_judicial.pdf",
    "codigo_comercio.pdf"
]

print("--- INICIANDO ACTUALIZACIÓN DE CONOCIMIENTO LEGAL (7 LIBROS) ---")

# 1. Verificar archivos locales
archivos_validos = []
nombres_encontrados = []

print("\n1. Verificando archivos en tu PC...")
for archivo in archivos_legales:
    if os.path.exists(archivo):
        archivos_validos.append(open(archivo, "rb"))
        nombres_encontrados.append(archivo)
        print(f"   ✅ Encontrado: {archivo}")
    else:
        print(f"   ⚠️  FALTA: '{archivo}' (Descárgalo y ponlo en la carpeta)")

if not archivos_validos:
    print("\n❌ No encontré ningún PDF. Ponlos en la carpeta y vuelve a intentar.")
    exit()

try:
    # 2. Buscar al Asistente LAI
    my_assistants = client.beta.assistants.list(order="desc", limit=20)
    target_assistant = next((a for a in my_assistants.data if "LAI" in a.name), None)
    
    if not target_assistant:
        print("\n❌ No se encontró el asistente LAI. Ejecuta main.py primero.")
        exit()
        
    print(f"\n2. 🤖 Asistente identificado: {target_assistant.name}")

    # 3. Gestión de la Biblioteca (Vector Store)
    vector_stores = client.beta.vector_stores.list()
    target_vs = next((vs for vs in vector_stores.data if "Biblioteca_Legal_Panama" in vs.name), None)

    if target_vs:
        print(f"3. 📚 Biblioteca existente encontrada ({target_vs.id}). Actualizando...")
    else:
        print("3. 📚 Creando nueva Biblioteca Legal desde cero...")
        target_vs = client.beta.vector_stores.create(name="Biblioteca_Legal_Panama")

    # 4. Subir los archivos a la Biblioteca
    print(f"\n4. ⬆️ Subiendo {len(archivos_validos)} libros legales a OpenAI... (Esto puede tardar unos segundos)")
    
    # Usamos upload_and_poll para esperar a que terminen de procesarse
    file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=target_vs.id,
        files=archivos_validos
    )
    
    print(f"   ✅ Carga completada. Estado: {file_batch.status}")
    print(f"   📊 Archivos procesados: {file_batch.file_counts}")

    # 5. Actualizar al Asistente para que use esta biblioteca
    print("\n5. 🔗 Conectando el cerebro de LAI a los nuevos libros...")
    client.beta.assistants.update(
        assistant_id=target_assistant.id,
        tool_resources={"file_search": {"vector_store_ids": [target_vs.id]}}
    )

    print("\n🎉 ¡ÉXITO TOTAL! LAI SYSTEM AHORA ES EXPERTO EN:")
    for n in nombres_encontrados:
        print(f"   - {n}")

except Exception as e:
    print(f"\n❌ Error crítico: {e}")