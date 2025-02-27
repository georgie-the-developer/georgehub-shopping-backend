import os
from werkzeug.utils import secure_filename
from datetime import datetime
import imghdr

class FileHandler:
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
        self.allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}

    def allowed_file(self, file):
        # Check file extension and mime type
        filename = secure_filename(file.filename)
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext[1:] not in self.allowed_extensions:
            return False
        return True

    def save_file(self, file, subfolder='products'):
        if file and self.allowed_file(file):
            # Create unique filename
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            unique_filename = f"{timestamp}_{filename}"
            
            # Create subfolder if it doesn't exist
            folder_path = os.path.join(self.upload_folder, subfolder)
            os.makedirs(folder_path, exist_ok=True)
            
            # Save file
            file_path = os.path.join(folder_path, unique_filename)
            file.save(file_path)
            
            # Return relative path for database storage
            return os.path.join(subfolder, unique_filename)
        return None

    def delete_file(self, file_path):
        if file_path:
            full_path = os.path.join(self.upload_folder, file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        return False