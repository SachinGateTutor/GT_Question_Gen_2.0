import schemdraw
import schemdraw.elements as elm
import schemdraw.logic as logic
import matplotlib
matplotlib.use('Agg')
import io
import traceback
import re
import os

def render(code: str, output_path: str):
    """Render schemdraw diagram with improved error handling"""
    
    try:
        # Post-process code for common AI mistakes (keeping the good parts from current system)
        code = code.replace('SchemDraw', 'schemdraw')
        
        # Check if code uses 'e.' elements before replacing the import
        uses_elements = re.search(r'\be\.\w+', code)
        
        # Only replace elements import if code doesn't use 'e.' elements
        if not uses_elements:
            code = code.replace('import schemdraw.elements as e', 'import schemdraw.logic as logic')
            code = code.replace('import SchemDraw.elements as e', 'import schemdraw.logic as logic')
        # Otherwise, keep the elements import but fix the library name
        else:
            code = code.replace('import SchemDraw.elements as e', 'import schemdraw.elements as e')
        
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
        
        # Fix color specifications for schemdraw elements
        code = re.sub(r'\.color\([\'"]([^\'"]*)[\'"]\)', r'.color("\1")', code)
        code = re.sub(r'\.fillcolor\([\'"]([^\'"]*)[\'"]\)', r'.fillcolor("\1")', code)
        
        # Fix common color issues - ensure colors are applied correctly
        code = re.sub(r'\.color\(([^)]+)\)\.label\(([^)]+)\)', r'.label(\2).color(\1)', code)
        code = re.sub(r'\.fillcolor\(([^)]+)\)\.label\(([^)]+)\)', r'.label(\2).fillcolor(\1)', code)
        
        # Ensure we have proper imports
        if 'import schemdraw' not in code:
            code = 'import schemdraw\nimport schemdraw.logic as logic\nfrom schemdraw import Drawing\n' + code
        
        # Add elements import if code uses 'e.' but doesn't have it
        if re.search(r'\be\.\w+', code) and 'import schemdraw.elements as e' not in code:
            # Insert after the first import line
            lines = code.split('\n')
            for i, line in enumerate(lines):
                if line.strip().startswith('import '):
                    lines.insert(i + 1, 'import schemdraw.elements as e')
                    break
            code = '\n'.join(lines)
            
        # Ensure we have a Drawing() call
        if 'd = Drawing()' not in code and 'd = schemdraw.Drawing()' not in code:
            code = code.replace('d = schem', 'd = schemdraw.Drawing()')
            if 'd = schemdraw.Drawing()' not in code:
                code = 'd = schemdraw.Drawing()\n' + code

        # Create buffer for image
        buffer = io.BytesIO()
        
        # Prepare execution environment with restricted globals
        exec_globals = {
            'schemdraw': schemdraw, 
            'elm': elm, 
            'logic': logic,
            'io': io, 
            'buffer': buffer,
            'd': None  # Will be created in the code
        }
        
        # Execute the diagram code
        print(f"🔍 Executing processed schemdraw code:\n{code}")
        exec(code, exec_globals)
        
        # Get the drawing object and save to buffer
        d = exec_globals.get('d')
        if d:
            try:
                d.save(buffer)
                buffer.seek(0)
                img = schemdraw.Image.open(buffer)
                print(f"Saving schemdraw image to: {os.path.abspath(output_path)}")
                img.save(output_path)
                print(f"✅ Schemdraw diagram saved as: {os.path.basename(output_path)}")
                return os.path.basename(output_path)
            except Exception as save_error:
                print(f"❌ Error saving schemdraw diagram: {save_error}")
                return None
        else:
            print("❌ No drawing object 'd' found in schemdraw code")
            return None
            
    except Exception as e:
        print(f'❌ Schemdraw diagram generation error: {e}')
        traceback.print_exc()
        return None 