import os
import uuid
from PIL import Image

def render_schemdraw_diagram(code, output_folder):
    import io
    import sys
    import traceback

    # Ensure the output directory exists
    os.makedirs(output_folder, exist_ok=True)

    filename = f"schemdraw_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(output_folder, filename)
    
    try:
        import schemdraw
        import schemdraw.elements as elm
        import schemdraw.logic as logic
        import matplotlib
        matplotlib.use('Agg')
        import re
        
        # Post-process code for common AI mistakes
        code = code.replace('SchemDraw', 'schemdraw')
        code = code.replace('import schemdraw.elements as e', 'import schemdraw.logic as logic')
        code = code.replace('import SchemDraw.elements as e', 'import schemdraw.logic as logic')
        code = code.replace('import schemdraw as schem', 'import schemdraw')
        code = code.replace('import SchemDraw as schem', 'import schemdraw')
        
        # Replace various AND gate patterns with logic.And()
        code = re.sub(r'e\.AND2|e\.And2|e\.and2|e\.And\(\)|e\.and\(\)|e\.andgate\(\)|e\.ANDGATE\(\)|e\.andgate\(\)', 'logic.And()', code)
        code = re.sub(r'd\.add\((.*?)\)', r'd += \1', code)
        
        # Fix all .save() patterns to use buffer
        code = re.sub(r'\.save\([\'"][^\'"]*[\'"]\)', '.save(buffer)', code)
        
        # Remove .output() calls which don't exist in schemdraw
        code = re.sub(r'\.output\(\)', '', code)
        code = re.sub(r'\.outputs\([^)]*\)', '', code)
        code = re.sub(r'\.inputs\([^)]*\)', '', code)
        code = re.sub(r'\.inputs\([^)]*\)\.outputs\([^)]*\)', '', code)
        
        # Replace schem.Drawing() with schemdraw.Drawing()
        code = code.replace('schem.Drawing()', 'schemdraw.Drawing()')
        
        # Replace d.draw() with d.save(buffer)
        code = code.replace('d.draw()', 'd.save(buffer)')

        # Remove assignment from 'd += ...' lines
        code = re.sub(r'\w+\s*=\s*d \+=', 'd +=', code)
        
        # Fix common syntax errors
        code = re.sub(r'd \+= e\.LINE.*?$', '# d += e.LINE  # Commented out invalid element', code, flags=re.MULTILINE)
        code = re.sub(r'd \+= e\.AND2.*?$', 'd += logic.And()', code, flags=re.MULTILINE)
        code = re.sub(r'd \+= e\.OR2.*?$', 'd += logic.Or()', code, flags=re.MULTILINE)
        
        # Fix invalid syntax like "d += e.LINE, d='left', l=d.unit"
        code = re.sub(r'd \+= e\.LINE.*?d=\'left\'.*?l=d\.unit.*?$', '# Invalid syntax commented out', code, flags=re.MULTILINE)
        
        # Ensure we have proper imports
        if 'import schemdraw' not in code:
            code = 'import schemdraw\nimport schemdraw.logic as logic\nfrom schemdraw import Drawing\n' + code
            
        # Ensure we have a Drawing() call
        if 'd = Drawing()' not in code and 'd = schemdraw.Drawing()' not in code:
            code = code.replace('d = schem', 'd = schemdraw.Drawing()')
            if 'd = schemdraw.Drawing()' not in code:
                code = 'd = schemdraw.Drawing()\n' + code

        # Create buffer for image
        buffer = io.BytesIO()
        
        # Prepare execution environment
        exec_globals = {
            'schemdraw': schemdraw, 
            'elm': elm, 
            'logic': logic,
            'io': io, 
            'buffer': buffer,
            'd': None  # Will be created in the code
        }
        
        # Execute the diagram code
        print(f"🔍 Executing processed code:\n{code}")
        exec(code, exec_globals)
        
        # Get the drawing object and save to buffer
        d = exec_globals.get('d')
        if d:
            try:
                d.save(buffer)
                buffer.seek(0)
                img = Image.open(buffer)
                print(f"Saving image to absolute path: {os.path.abspath(filepath)}")
                img.save(filepath)
                print(f"✅ Diagram saved as: {filename}")
                return filename
            except Exception as save_error:
                print(f"❌ Error saving diagram: {save_error}")
                return None
        else:
            print("❌ No drawing object 'd' found in code")
            return None
            
    except Exception as e:
        print(f'❌ Diagram generation error: {e}')
        traceback.print_exc()
        return None 