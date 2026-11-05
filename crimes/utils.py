# crimes/utils.py
import hashlib
from PIL import Image
import io

def generate_image_hash(image_field):
    """Generate SHA256 hash of uploaded image"""
    try:
        img = Image.open(image_field)
        
        # Convert to grayscale and resize for consistent hashing
        img = img.convert('L').resize((64, 64), Image.Resampling.LANCZOS)
        
        # Convert to bytes
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_bytes = img_byte_arr.getvalue()
        
        return hashlib.sha256(img_bytes).hexdigest()
    except Exception as e:
        print(f"Error generating image hash: {e}")
        return ''

def compare_biometrics(photo_hash, thumb_hash=None):
    """Compare biometrics with criminal database"""
    from .models import CriminalRecord
    
    matches = []
    
    if photo_hash:
        # Check for exact photo hash match
        criminals = CriminalRecord.objects.filter(photo_hash=photo_hash)
        for criminal in criminals:
            matches.append({
                'criminal': criminal,
                'match_type': 'Photo',
                'confidence': 95
            })
    
    if thumb_hash:
        # Check for exact fingerprint hash match
        criminals = CriminalRecord.objects.filter(fingerprint_hash=thumb_hash)
        for criminal in criminals:
            matches.append({
                'criminal': criminal,
                'match_type': 'Fingerprint',
                'confidence': 98
            })
    
    return matches