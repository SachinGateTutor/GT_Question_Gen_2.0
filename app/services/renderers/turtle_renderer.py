import turtle
import os
import traceback
import io
from PIL import Image

def render(code: str, output_path: str):
    """Render turtle diagram with improved error handling"""
    
    try:
        # Create buffer
        buffer = io.BytesIO()
        
        # Prepare execution environment
        exec_globals = {
            'turtle': turtle,
            'buffer': buffer
        }
        
        print(f"🔍 Executing turtle code:\n{code}")
        exec(code, exec_globals)
        
        # Save image
        img = Image.open(buffer)
        img.save(output_path)
        print(f"✅ Turtle diagram saved as: {os.path.basename(output_path)}")
        return os.path.basename(output_path)
        
    except Exception as e:
        print(f'❌ Turtle diagram generation error: {e}')
        traceback.print_exc()
        return None 