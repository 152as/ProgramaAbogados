import os
import time
import base64
import cv2 # IMPORTANTE: Necesitas pip install opencv-python
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class AIAssistantManager:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.assistant_id = None
        self.thread_id = None
        self.constitution_file_id = None 
        # Memoria de archivos por hilo
        self.files_per_thread = {} 

        self._find_or_upload_constitution()
        self._get_or_create_assistant()
        self.nuevo_hilo()

    def nuevo_hilo(self):
        """Crea un hilo nuevo para un chat limpio."""
        try:
            self.thread_id = self.client.beta.threads.create().id
            self.files_per_thread[self.thread_id] = []
            return self.thread_id
        except: return None

    def set_thread(self, thread_id):
        """Recupera un chat anterior."""
        self.thread_id = thread_id
        if thread_id not in self.files_per_thread:
            self.files_per_thread[thread_id] = []

    def _find_or_upload_constitution(self):
        try:
            nombres = ["constitucion_panama.pdf", "constitucion_panama.pdf.pdf"]
            files = self.client.files.list()
            for f in files.data:
                if f.filename in nombres:
                    self.constitution_file_id = f.id
                    return
        except: pass

    def _get_or_create_assistant(self):
        # --- AQUÍ ESTÁ LA ACTUALIZACIÓN DE LOS CÓDIGOS ---
        instructions = (
            "Eres LAI, un auditor legal experto en leyes de Panamá.\n\n"
            "TU LÓGICA DE TRABAJO ES ESTRICTA:\n"
            "1. **VISIÓN DE IMÁGENES:** Si el usuario sube una imagen (foto de boleta, accidente, contrato), analízala visualmente con EXTREMA PRECISIÓN. Extrae números de boleta, fechas, firmas y códigos de infracción.\n"
            "2. **BASE DE CONOCIMIENTO COMPLETA:** Tienes acceso en tu 'Vector Store' a la legislación completa de Panamá:\n"
            "   - **Constitución Política**\n"
            "   - **Reglamento de Tránsito Vehicular**\n"
            "   - **Código Penal**\n"
            "   - **Código Procesal Penal**\n"
            "   - **Código Judicial**\n"
            "   - **Código de Comercio**\n"
            "   - **Código de Trabajo**\n"
            "   - **Código de la Familia**\n"
            "   Úsalos para fundamentar cualquier respuesta legal.\n"
            "3. **SI EL USUARIO PREGUNTA POR 'EL DOCUMENTO' O 'EL CASO':**\n"
            "   - Verifica si tienes archivos adjuntos en el 'code_interpreter'.\n"
            "   - SI NO HAY ARCHIVOS: Responde 'No has subido ningún documento PDF en este chat todavía. Por favor súbelo para analizarlo'.\n"
            "   - SI HAY ARCHIVOS: Usa 'code_interpreter' para leer el texto real del PDF y responder.\n\n"
            "4. **SI EL USUARIO HACE PREGUNTAS LEGALES (¿Es legal esto?):**\n"
            "   - Si hay un PDF subido: Analiza el PDF, luego BUSCA en tus leyes (file_search) los artículos relevantes y CRUZA la información.\n"
            "   - Si es un tema de Tránsito (multas, accidentes, placas): Prioriza buscar en el Reglamento de Tránsito.\n"
            "   - Si es un tema laboral, penal o de familia: Busca en el Código correspondiente.\n\n"
            "5. **GENERACIÓN DE DOCUMENTOS:** Si el usuario te pide 'Generar Escrito' o 'Redactar', compórtate como un abogado redactor. Crea el documento formal."
        )
        try:
            my_assts = self.client.beta.assistants.list(limit=20)
            existing = next((a for a in my_assts.data if "LAI" in a.name), None)
            tools = [{"type": "file_search"}, {"type": "code_interpreter"}]
            if existing:
                self.assistant_id = existing.id
                # Actualizamos las instrucciones del asistente existente
                self.client.beta.assistants.update(assistant_id=self.assistant_id, instructions=instructions, tools=tools, model="gpt-4o")
            else:
                self.assistant_id = self.client.beta.assistants.create(name="LAI Auditor V21 (Full Codes)", instructions=instructions, model="gpt-4o", tools=tools).id
        except: pass

    def _cancelar_runs_activos(self):
        if not self.thread_id: return
        try:
            runs = self.client.beta.threads.runs.list(thread_id=self.thread_id)
            for run in runs.data:
                if run.status in ['in_progress', 'queued', 'requires_action']:
                    self.client.beta.threads.runs.cancel(thread_id=self.thread_id, run_id=run.id)
                    time.sleep(1)
        except: pass

    def _procesar_respuesta_segura(self, messages):
        """Evita el error de ImageFileContentBlock leyendo bloque por bloque."""
        try:
            if not messages.data: return "..."
            
            msg = messages.data[0]
            texto_final = ""
            
            # Recorremos los bloques de contenido
            for content_block in msg.content:
                if content_block.type == 'text':
                    texto_final += content_block.text.value
                elif content_block.type == 'image_file':
                    texto_final += "\n\n[ 📊 La IA ha generado un gráfico visual del caso. ]\n\n"
            
            return texto_final
        except Exception as e:
            return f"Error leyendo respuesta: {str(e)}"

    # --- FUNCIÓN: LIMPIEZA DE IMAGEN CON OPENCV ---
    def _preprocesar_imagen(self, input_path):
        """Mejora la imagen para OCR: Escala de grises + Contraste + Eliminación de Ruido"""
        try:
            # Leer imagen
            img = cv2.imread(input_path)
            if img is None: return input_path # Si falla leer, devolver original

            # 1. Escala de Grises
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            # 2. Eliminación de Ruido (Denoising)
            # h=10 es la fuerza del filtro. Mayor número = más borroso pero menos ruido.
            denoised = cv2.fastNlMeansDenoising(gray, h=10)

            # 3. Aumentar Contraste (Histogram Equalization Adaptativo - CLAHE)
            # Esto hace que el texto resalte incluso si hay sombras en el papel
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            contrast = clahe.apply(denoised)

            # Guardar imagen procesada temporalmente
            base, ext = os.path.splitext(input_path)
            output_path = f"{base}_proc{ext}"
            cv2.imwrite(output_path, contrast)
            
            return output_path
        except Exception as e:
            print(f"[IA Vision] Error pre-procesando: {e}")
            return input_path # Si falla algo, usamos la original sin miedo

    def procesar_archivo(self, file_path):
        if not self.client or not self.thread_id: return False, "Error de API Key"
        
        # Detectar si es Imagen o PDF
        ext = os.path.splitext(file_path)[1].lower()
        es_imagen = ext in ['.jpg', '.jpeg', '.png']

        try:
            # Subir archivo a OpenAI
            user_file = self.client.files.create(file=open(file_path, "rb"), purpose="assistants" if not es_imagen else "vision")
            
            if not es_imagen:
                # Si es PDF, lo añadimos al Code Interpreter como siempre
                if self.thread_id not in self.files_per_thread:
                    self.files_per_thread[self.thread_id] = []
                self.files_per_thread[self.thread_id].append(user_file.id)

                self.client.beta.threads.update(
                    thread_id=self.thread_id,
                    tool_resources={
                        "code_interpreter": {"file_ids": self.files_per_thread[self.thread_id]}
                    }
                )
                return True, "Documento PDF analizado."
            else:
                # Si es IMAGEN, no se añade al interpreter, se enviará en el mensaje
                return True, "Imagen procesada visualmente."

        except Exception as e:
            return False, f"Error técnico: {str(e)}"

    def enviar_mensaje(self, texto_usuario, imagen_path=None):
        if not self.thread_id: return "Error: No hay chat activo."
        self._cancelar_runs_activos()
        
        content_payload = []
        
        # 1. Añadir texto del usuario
        archivos = len(self.files_per_thread.get(self.thread_id, []))
        contexto = f"\n[SISTEMA: Hay {archivos} PDF cargados.]" if archivos > 0 else ""
        content_payload.append({"type": "text", "text": texto_usuario + contexto})

        # 2. Si hay IMAGEN reciente para enviar
        if imagen_path:
            try:
                # APLICAMOS LA MEJORA DE IMAGEN AQUÍ
                imagen_optimizada = self._preprocesar_imagen(imagen_path)
                
                # Subir imagen (usamos la optimizada si se creó, o la original si falló)
                file_obj = self.client.files.create(file=open(imagen_optimizada, "rb"), purpose="vision")
                
                # Referenciarla en el mensaje con detalle ALTO
                content_payload = [
                    {"type": "text", "text": texto_usuario + " [Analiza esta evidencia visual con máximo detalle]"},
                    {
                        "type": "image_file",
                        "image_file": {"file_id": file_obj.id, "detail": "high"} # Forzamos modo HD
                    }
                ]
            except: pass

        try:
            self.client.beta.threads.messages.create(
                thread_id=self.thread_id, 
                role="user", 
                content=content_payload # Enviamos lista mixta (texto + imagen)
            )
            
            run = self.client.beta.threads.runs.create(thread_id=self.thread_id, assistant_id=self.assistant_id)
            
            while run.status in ['queued', 'in_progress', 'cancelling']:
                time.sleep(0.5)
                run = self.client.beta.threads.runs.retrieve(thread_id=self.thread_id, run_id=run.id)

            if run.status == 'completed':
                messages = self.client.beta.threads.messages.list(thread_id=self.thread_id)
                return self._procesar_respuesta_segura(messages)
            
            return f"Error IA: {run.last_error or run.status}"
        except Exception as e: return f"Error: {str(e)}"

    def generar_titulo_contextual(self, p, r):
        return "Consulta Legal"