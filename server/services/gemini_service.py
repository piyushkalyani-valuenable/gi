"""
Gemini AI service for chat and document processing
"""
import io
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from google import genai
from google.genai import types
from config.settings import settings
from config.constants import GEMINI_REQUEST_TIMEOUT


class GeminiService:
    """Service for interacting with Gemini AI"""
    
    def __init__(self):
        self.client = genai.Client(api_key=settings.gemini_api_key)
        
        # Available Gemini Models (as of Nov 2025):
        # 
        # BEST QUALITY (for complex reasoning):
        # - gemini-3-pro-preview          : Best multimodal understanding, most powerful
        # 
        # BALANCED (good quality + speed):
        # - gemini-2.5-pro-preview-06-05  : Great reasoning, good for documents
        # - gemini-2.5-flash              : Fast with good quality
        # 
        # FASTEST (cost-efficient, high throughput):
        # - gemini-2.5-flash-lite         : Fastest, optimized for cost-efficiency
        # - gemini-2.0-flash              : Previous gen fast model
        
        # Using Flash-Lite for now (fast + cost-efficient)
        # self.model = "gemini-2.5-flash-lite"
        
        # Uncomment for better quality (slower, more expensive):
        self.model = "gemini-3-pro-preview"
        
        self.executor = ThreadPoolExecutor(max_workers=5)
    
    def chat(self, message: str) -> str:
        """
        Send a text message to Gemini with timeout
        
        Args:
            message: User message
        
        Returns:
            Gemini's response text
        """
        def _make_request():
            response = self.client.models.generate_content(
                model=self.model,
                contents=message
            )
            return response.text.strip()
        
        try:
            future = self.executor.submit(_make_request)
            return future.result(timeout=GEMINI_REQUEST_TIMEOUT)
        except FuturesTimeoutError:
            print(f"Gemini timeout after {GEMINI_REQUEST_TIMEOUT} seconds")
            raise Exception(f"Gemini API request timed out after {GEMINI_REQUEST_TIMEOUT} seconds")
        except Exception as e:
            print(f"Gemini error: {e}")
            raise
    
    def chat_with_file(self, message: str, file_data: bytes, filename: str) -> str:
        """
        Send a message with a file to Gemini with timeout.
        File is automatically deleted from Google storage after processing.
        
        Args:
            message: Prompt/instruction
            file_data: File bytes
            filename: Original filename (used for mime type detection)
        
        Returns:
            Gemini's response text
        """
        gemini_file_name = None
        
        try:
            # Determine mime type
            mime_type = self._get_mime_type(filename)
            
            # Upload file to Gemini
            file_io = io.BytesIO(file_data)
            file_io.name = filename
            
            upload_config = types.UploadFileConfig(mime_type=mime_type)
            gemini_file = self.client.files.upload(file=file_io, config=upload_config)
            gemini_file_name = gemini_file.name  # Store for cleanup
            
            print(f"📤 Uploaded file to Gemini: {gemini_file_name}")
            
            # Poll until file is ready
            self._wait_for_file_ready(gemini_file_name)
            
            # Send message with file
            response = self.client.models.generate_content(
                model=self.model,
                contents=[gemini_file, message]
            )
            
            return response.text.strip()
            
        except TimeoutError as e:
            print(f"Gemini file processing timeout: {e}")
            raise Exception(f"Gemini file processing timed out")
        except Exception as e:
            print(f"Gemini file chat error: {e}")
            raise
        finally:
            # ALWAYS cleanup uploaded file to avoid storage charges
            if gemini_file_name:
                self._delete_file(gemini_file_name)
    
    def _delete_file(self, file_name: str):
        """Delete file from Google storage to avoid charges"""
        try:
            self.client.files.delete(name=file_name)
            print(f"🗑️ Deleted file from Gemini storage: {file_name}")
        except Exception as e:
            print(f"⚠️ Failed to delete file {file_name}: {e}")
            # Log but don't raise - best effort cleanup
    
    def _get_mime_type(self, filename: str) -> str:
        """Determine mime type from filename"""
        lower = filename.lower()
        if lower.endswith('.pdf'):
            return 'application/pdf'
        elif lower.endswith('.png'):
            return 'image/png'
        elif lower.endswith(('.jpg', '.jpeg')):
            return 'image/jpeg'
        elif lower.endswith('.gif'):
            return 'image/gif'
        elif lower.endswith('.webp'):
            return 'image/webp'
        elif lower.endswith('.avif'):
            return 'image/avif'
        else:
            return 'application/octet-stream'
    
    def _wait_for_file_ready(self, file_name: str, timeout: int = 60):
        """Poll until file is processed and ready"""
        start_time = time.time()
        poll_interval = 2
        
        while (time.time() - start_time) < timeout:
            file_status = self.client.files.get(name=file_name)
            if file_status.state == 'ACTIVE':
                return
            time.sleep(poll_interval)
        
        raise TimeoutError(f"File processing timed out after {timeout} seconds")
    
    def cleanup_all_files(self) -> dict:
        """
        Delete ALL files from Google storage.
        Use this to clean up orphaned files and reduce storage costs.
        
        Returns:
            Dict with deleted count and any errors
        """
        deleted = 0
        errors = []
        
        try:
            # List all files in storage
            files = self.client.files.list()
            
            for file in files:
                try:
                    self.client.files.delete(name=file.name)
                    print(f"🗑️ Deleted: {file.name}")
                    deleted += 1
                except Exception as e:
                    errors.append(f"{file.name}: {e}")
            
            print(f"✅ Cleanup complete: {deleted} files deleted")
            
        except Exception as e:
            errors.append(f"Failed to list files: {e}")
        
        return {
            "deleted_count": deleted,
            "errors": errors
        }
