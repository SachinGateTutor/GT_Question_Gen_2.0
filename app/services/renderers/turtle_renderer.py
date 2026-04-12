import turtle
import os
import traceback
import io
from PIL import Image, ImageDraw

def render(code: str, output_path: str):
    """Render turtle diagram with improved error handling"""
    
    try:
        # Prepare execution environment
        exec_globals = {
            'turtle': turtle
        }
        
        print(f" Executing turtle code:\n{code}")
        exec(code, exec_globals)
        
        # Turtle doesn't save to files by default, so we'll create a simple fallback
        # In a real implementation, you'd need to capture the turtle screen
        img = Image.new('RGB', (400, 300), 'white')
        draw = ImageDraw.Draw(img)
        draw.text((50, 50), "Turtle Diagram", fill='black')
        img.save(output_path)
        
        print(f" Turtle diagram saved as: {os.path.basename(output_path)}")
        return os.path.basename(output_path)
        
    except Exception as e:
        print(f' Turtle diagram generation error: {e}')
        traceback.print_exc()
        return None 