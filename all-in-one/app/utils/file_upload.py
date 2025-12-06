import os
import uuid
from fastapi import UploadFile, HTTPException
from typing import Optional
from PIL import Image
import io
from app.config import settings
import magic

async def validate_image(file: UploadFile) -> None:
    """Validate uploaded image file"""
    # Check file size
    content = await file.read()
    if len(content) > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max size: {settings.MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    # Check MIME type
    mime_type = magic.from_buffer(content, mime=True)
    if mime_type not in settings.ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_IMAGE_TYPES)}"
        )
    
    # Reset file pointer
    await file.seek(0)
    
    # Validate image with PIL
    try:
        image = Image.open(io.BytesIO(content))
        image.verify()
        await file.seek(0)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file")

async def upload_file(
    file: UploadFile,
    folder: str = "uploads",
    allowed_types: Optional[list] = None,
    max_size: Optional[int] = None
) -> str:
    """Upload file to server and return URL"""
    if allowed_types is None:
        allowed_types = settings.ALLOWED_IMAGE_TYPES
    
    if max_size is None:
        max_size = settings.MAX_UPLOAD_SIZE
    
    # Create directory if not exists
    upload_dir = os.path.join(settings.UPLOAD_DIR, folder)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Generate unique filename
    ext = os.path.splitext(file.filename)[1]
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(upload_dir, filename)
    
    # Save file
    content = await file.read()
    
    # Validate size
    if len(content) > max_size:
        raise HTTPException(
            status_code=413,
            detail="File too large"
        )
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Generate URL (in production, use CDN URL)
    file_url = f"/static/{folder}/{filename}"
    
    return file_url

async def optimize_image(
    file_path: str,
    max_width: int = 1200,
    max_height: int = 800,
    quality: int = 85
) -> str:
    """Optimize image size and quality"""
    try:
        with Image.open(file_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            
            # Resize if too large
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
            
            # Save optimized image
            optimized_path = file_path.replace('.', '_optimized.')
            img.save(optimized_path, 'JPEG' if file_path.lower().endswith('.jpg') else 'PNG', 
                    quality=quality, optimize=True)
            
            # Replace original with optimized
            os.replace(optimized_path, file_path)
            
            return file_path
            
    except Exception as e:
        print(f"Error optimizing image: {e}")
        return file_path

def delete_file(file_url: str) -> bool:
    """Delete file from server"""
    try:
        # Extract file path from URL
        if file_url.startswith('/static/'):
            file_path = os.path.join(settings.UPLOAD_DIR, file_url[8:])
        else:
            file_path = file_url
        
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
        return False
    except Exception:
        return False