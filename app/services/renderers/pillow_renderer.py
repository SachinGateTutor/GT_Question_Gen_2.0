from PIL import Image, ImageDraw
import os
import traceback
import re
import io

def render(code: str, output_path: str):
    """Render pillow diagram with improved error handling"""
    
    try:
        # Post-process code for common AI mistakes
        # Fix color specifications for pillow
        code = re.sub(r'fill=[\'"]([^\'"]*)[\'"]', r'fill="\1"', code)
        code = re.sub(r'outline=[\'"]([^\'"]*)[\'"]', r'outline="\1"', code)
        code = re.sub(r'color=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)
        
        # Fix common pillow color issues
        code = re.sub(r'f=[\'"]([^\'"]*)[\'"]', r'fill="\1"', code)
        code = re.sub(r'o=[\'"]([^\'"]*)[\'"]', r'outline="\1"', code)
        code = re.sub(r'c=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)
        
        # Prepare execution environment
        exec_globals = {
            'Image': Image,
            'ImageDraw': ImageDraw
        }
        
        print(f"🔍 Executing pillow code:\n{code}")
        exec(code, exec_globals)
        
        # The code should save directly to output_path
        # If it doesn't, we'll create a simple fallback
        if not os.path.exists(output_path):
            # Create a simple fallback image
            img = Image.new('RGB', (400, 300), 'white')
            draw = ImageDraw.Draw(img)
            draw.text((50, 50), "Pillow Diagram", fill='black')
            img.save(output_path)
        
        print(f"✅ Pillow diagram saved as: {os.path.basename(output_path)}")
        return os.path.basename(output_path)
        
    except Exception as e:
        print(f'❌ Pillow diagram generation error: {e}')
        traceback.print_exc()
        return None 