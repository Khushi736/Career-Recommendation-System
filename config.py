# config.py
import os

class Config:
    # Base directory
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    
    # Single upload folder for all files
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    
    # Subdirectories within uploads
    RESUME_FOLDER = os.path.join(UPLOAD_FOLDER, 'resumes')
    PROFILE_PICS_FOLDER = os.path.join(UPLOAD_FOLDER, 'profile_pics')
    TEMP_FOLDER = os.path.join(UPLOAD_FOLDER, 'temp')
    
    # Allowed extensions
    ALLOWED_RESUME_EXTENSIONS = {'pdf', 'doc', 'docx'}
    ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # Max file sizes (5MB for images, 10MB for resumes)
    MAX_IMAGE_SIZE = 5 * 1024 * 1024
    MAX_RESUME_SIZE = 10 * 1024 * 1024
    
    @staticmethod
    def init_upload_folders():
        """Initialize only the single upload folder structure"""
        folders = [
            Config.UPLOAD_FOLDER,
            Config.RESUME_FOLDER,
            Config.PROFILE_PICS_FOLDER,
            Config.TEMP_FOLDER
        ]
        for folder in folders:
            os.makedirs(folder, exist_ok=True)
        print(f"✅ Upload folders initialized at: {Config.UPLOAD_FOLDER}")