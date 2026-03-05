import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

class DatabaseHandler:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_KEY")
        self.supabase: Client = None

        if self.url and self.key:
            try:
                self.supabase = create_client(self.url, self.key)
            except Exception as e:
                print(f"[DB ERROR] Conexión fallida: {e}")

    def registrar_documento(self, nombre_archivo, thread_id, info_extra=""):
        """Registra un chat y lo vincula a un Thread ID de OpenAI."""
        if not self.supabase: return None
        try:
            data = {
                "nombre_archivo": nombre_archivo,
                "resumen_ia": info_extra,
                "thread_id": thread_id,
                "archivado": False
            }
            response = self.supabase.table("documentos").insert(data).execute()
            
            if response.data:
                return response.data[0]['id']
            return None
        except Exception as e:
            print(f"[DB ERROR] Guardar documento: {e}")
            return None

    def guardar_mensaje(self, doc_id, rol, contenido):
        if not self.supabase or not doc_id: return
        try:
            data = {"documento_id": doc_id, "rol": rol, "contenido": contenido}
            self.supabase.table("mensajes").insert(data).execute()
        except Exception as e:
            print(f"[DB ERROR] Guardar mensaje: {e}")

    def recuperar_chat_completo(self, doc_id):
        if not self.supabase: return []
        try:
            # Ordenamos por fecha para que el chat tenga sentido
            return self.supabase.table("mensajes").select("*").eq("documento_id", doc_id).order("fecha", desc=False).execute().data
        except: return []

    def obtener_activos(self):
        if not self.supabase: return []
        try:
            return self.supabase.table("documentos").select("*").eq("archivado", False).order("fecha_subida", desc=True).limit(20).execute().data
        except: return []

    def obtener_archivados(self):
        if not self.supabase: return []
        try:
            return self.supabase.table("documentos").select("*").eq("archivado", True).order("fecha_subida", desc=True).execute().data
        except: return []

    def actualizar_titulo(self, nombre_archivo_o_id, nuevo_titulo):
        if not self.supabase: return
        try:
            # Soporte flexible para actualizar por ID (int) o nombre (str)
            if isinstance(nombre_archivo_o_id, int) or str(nombre_archivo_o_id).isdigit():
                 self.supabase.table("documentos").update({"resumen_ia": nuevo_titulo}).eq("id", int(nombre_archivo_o_id)).execute()
            else:
                 self.supabase.table("documentos").update({"resumen_ia": nuevo_titulo}).eq("nombre_archivo", str(nombre_archivo_o_id)).execute()
        except: pass

    def archivar_documento(self, id_doc, estado=True):
        if not self.supabase: return
        try:
            self.supabase.table("documentos").update({"archivado": estado}).eq("id", id_doc).execute()
        except: pass

    def eliminar_definitivamente(self, id_doc):
        if not self.supabase: return
        try:
            self.supabase.table("documentos").delete().eq("id", id_doc).execute()
        except: pass