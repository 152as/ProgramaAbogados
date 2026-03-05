import os
import shutil
import fitz
from datetime import datetime

class DocumentManager:
    def __init__(self, upload_dir="storage/uploads"):
        self.upload_dir = upload_dir
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)

    def save_to_local(self, file_path):
        try:
            if not file_path.lower().endswith('.pdf'): return None
            file_name = os.path.basename(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_name = f"{timestamp}_{file_name}"
            dest_path = os.path.join(self.upload_dir, new_name)
            shutil.copy(file_path, dest_path)
            return dest_path
        except: return None