"""
utils/image_capture.py - Utility untuk mengambil gambar dari folder
"""

import os
import shutil
from datetime import datetime
from config import IMAGE_EXTENSIONS, CAPTURED_DIR


class ImageCapture:
    """Class untuk mengelola pengambilan gambar dari folder"""
    
    def __init__(self):
        self.captured_dir = CAPTURED_DIR
        os.makedirs(self.captured_dir, exist_ok=True)
    
    def get_latest_image(self, folder_path, since_timestamp=None):
        """
        Mendapatkan gambar terbaru dari folder
        
        Args:
            folder_path: Path ke folder gambar
            since_timestamp: Only return images with mtime >= this value (unix timestamp).
                             If None, returns the overall newest image.
            
        Returns:
            tuple: (success, file_path or error_message)
        """
        if not folder_path or not os.path.exists(folder_path):
            return False, f"Folder tidak ditemukan: {folder_path}"
        
        try:
            # Get semua file gambar
            image_files = []
            for file in os.listdir(folder_path):
                ext = os.path.splitext(file)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    full_path = os.path.join(folder_path, file)
                    if os.path.isfile(full_path):
                        mtime = os.path.getmtime(full_path)
                        # Filter: only fresh images if since_timestamp given
                        if since_timestamp is not None and mtime < since_timestamp:
                            continue
                        image_files.append((full_path, mtime))
            
            if not image_files:
                if since_timestamp is not None:
                    return False, "Tidak ada gambar baru sejak trigger"
                return False, "Tidak ada file gambar di folder"
            
            # Sort by modification time (newest first)
            image_files.sort(key=lambda x: x[1], reverse=True)
            
            # Return newest
            newest_file = image_files[0][0]
            return True, newest_file
            
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def capture_and_copy(self, source_folder, prefix="IMG", since_timestamp=None):
        """
        Ambil gambar terbaru (fresh) dan copy ke folder captured
        
        Args:
            source_folder: Folder sumber gambar
            prefix: Prefix untuk nama file baru
            since_timestamp: Only accept images with mtime >= this (unix timestamp)
            
        Returns:
            tuple: (success, new_file_path or error_message)
        """
        success, result = self.get_latest_image(source_folder, since_timestamp=since_timestamp)
        
        if not success:
            return False, result
        
        try:
            # Generate nama file baru
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            ext = os.path.splitext(result)[1]
            new_filename = f"{prefix}_{timestamp}{ext}"
            new_path = os.path.join(self.captured_dir, new_filename)
            
            # Copy file
            shutil.copy2(result, new_path)
            
            return True, new_path
            
        except Exception as e:
            return False, f"Error copying: {str(e)}"

    
    def get_image_info(self, image_path):
        """Mendapatkan info gambar"""
        if not image_path or not os.path.exists(image_path):
            return None
        
        try:
            stat = os.stat(image_path)
            return {
                "path": image_path,
                "filename": os.path.basename(image_path),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S")
            }
        except:
            return None
    
    def list_images_in_folder(self, folder_path, limit=10):
        """List gambar di folder (terbaru dulu)"""
        if not folder_path or not os.path.exists(folder_path):
            return []
        
        try:
            image_files = []
            for file in os.listdir(folder_path):
                ext = os.path.splitext(file)[1].lower()
                if ext in IMAGE_EXTENSIONS:
                    full_path = os.path.join(folder_path, file)
                    if os.path.isfile(full_path):
                        mtime = os.path.getmtime(full_path)
                        image_files.append({
                            "path": full_path,
                            "filename": file,
                            "modified": mtime
                        })
            
            # Sort by modification time
            image_files.sort(key=lambda x: x["modified"], reverse=True)
            
            return image_files[:limit]
            
        except:
            return []