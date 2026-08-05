import os
import shutil

def cleanup_upload_folders():
    """Remove duplicate upload folders"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    
    folders_to_remove = [
        os.path.join(base_dir, 'uploads', 'resumes'),
        os.path.join(base_dir, 'temp_uploads'),
        os.path.join(base_dir, 'static', 'uploads')
    ]
    
    for folder in folders_to_remove:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"🗑️ Removed: {folder}")
    
    # Ensure main uploads folder exists
    main_uploads = os.path.join(base_dir, 'uploads')
    os.makedirs(main_uploads, exist_ok=True)
    print(f"✅ Main uploads folder ready: {main_uploads}")

if __name__ == '__main__':
    cleanup_upload_folders()