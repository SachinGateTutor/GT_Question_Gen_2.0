import os
import uuid
from PIL import Image
import io
import sys
import traceback

def render_diagram(code, library_name, output_folder):
    """Render diagram using the specified library"""
    
    # Ensure the output directory exists
    os.makedirs(output_folder, exist_ok=True)
    
    filename = f"{library_name}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(output_folder, filename)
    
    try:
        if library_name == 'schemdraw':
            return render_schemdraw_diagram(code, output_folder)
        elif library_name == 'matplotlib':
            return render_matplotlib_diagram(code, output_folder)
        elif library_name == 'networkx':
            return render_networkx_diagram(code, output_folder)
        elif library_name == 'graphviz':
            return render_graphviz_diagram(code, output_folder)
        elif library_name == 'plotly':
            return render_plotly_diagram(code, output_folder)
        elif library_name == 'seaborn':
            return render_seaborn_diagram(code, output_folder)
        elif library_name == 'pillow':
            return render_pillow_diagram(code, output_folder)
        elif library_name == 'turtle':
            return render_turtle_diagram(code, output_folder)
        else:
            print(f"❌ Unknown library: {library_name}, falling back to schemdraw")
            return render_schemdraw_diagram(code, output_folder)
            
    except Exception as e:
        print(f'❌ Diagram generation error for {library_name}: {e}')
        traceback.print_exc()
        return None

def render_schemdraw_diagram(code, output_folder):
    """Original schemdraw rendering logic"""
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
        print(f"🔍 Executing processed schemdraw code:\n{code}")
        exec(code, exec_globals)
        
        # Get the drawing object and save to buffer
        d = exec_globals.get('d')
        if d:
            try:
                d.save(buffer)
                buffer.seek(0)
                img = Image.open(buffer)
                print(f"Saving schemdraw image to: {os.path.abspath(filepath)}")
                img.save(filepath)
                print(f"✅ Schemdraw diagram saved as: {filename}")
                return filename
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

def render_matplotlib_diagram(code, output_folder):
    """Render matplotlib diagram"""
    filename = f"matplotlib_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(output_folder, filename)
    
    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        import pandas as pd
        
        # Post-process code for common AI mistakes
        # Add missing imports if needed
        if 'np.' in code and 'import numpy' not in code:
            code = 'import numpy as np\n' + code
        if 'pd.' in code and 'import pandas' not in code:
            code = 'import pandas as pd\n' + code
            
        # Fix common matplotlib issues
        if 'plt.show()' in code:
            code = code.replace('plt.show()', '# plt.show()  # Not needed for saving')
        
        # Fix BytesIO references
        code = code.replace('BytesIO()', 'io.BytesIO()')
        code = code.replace('from io import BytesIO', '')
        
        # Create buffer
        buffer = io.BytesIO()
        
        # Prepare execution environment
        exec_globals = {
            'plt': plt,
            'np': np,
            'pd': pd,
            'buffer': buffer,
            'io': io
        }
        
        print(f"🔍 Executing matplotlib code:\n{code}")
        exec(code, exec_globals)
        
        # Save image
        img = Image.open(buffer)
        img.save(filepath)
        print(f"✅ Matplotlib diagram saved as: {filename}")
        return filename
        
    except Exception as e:
        print(f'❌ Matplotlib diagram generation error: {e}')
        traceback.print_exc()
        return None

def render_networkx_diagram(code, output_folder):
    """Render networkx diagram"""
    filename = f"networkx_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(output_folder, filename)
    
    try:
        import networkx as nx
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        
        # Create buffer
        buffer = io.BytesIO()
        
        # Prepare execution environment
        exec_globals = {
            'nx': nx,
            'plt': plt,
            'buffer': buffer
        }
        
        print(f"🔍 Executing networkx code:\n{code}")
        exec(code, exec_globals)
        
        # Save image
        img = Image.open(buffer)
        img.save(filepath)
        print(f"✅ Networkx diagram saved as: {filename}")
        return filename
        
    except Exception as e:
        print(f'❌ Networkx diagram generation error: {e}')
        traceback.print_exc()
        return None

def render_graphviz_diagram(code, output_folder):
    """Render graphviz diagram"""
    filename = f"graphviz_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(output_folder, filename)
    
    try:
        import graphviz
        import tempfile
        import glob
        
        # Post-process code for common AI mistakes
        # Fix the render method call - graphviz doesn't accept BytesIO directly
        if 'dot.render(buffer, format=' in code:
            code = code.replace('dot.render(buffer, format=\'png\', cleanup=True)', 
                              'dot.render(tempfile.mktemp(), format=\'png\', cleanup=True)')
        
        # Create buffer
        buffer = io.BytesIO()
        
        # Prepare execution environment
        exec_globals = {
            'graphviz': graphviz,
            'buffer': buffer,
            'tempfile': tempfile,
            'os': os
        }
        
        print(f"🔍 Executing graphviz code:\n{code}")
        exec(code, exec_globals)
        
        # Graphviz saves to a file, so we need to read it back
        # The dot object should have been created in the code
        dot = exec_globals.get('dot')
        if dot:
            # Save to a temporary file
            temp_path = tempfile.mktemp(suffix='')
            dot.render(temp_path, format='png', cleanup=True)
            
            # Graphviz creates files with .png extension
            actual_file = temp_path + '.png'
            
            # Read the generated file into buffer
            if os.path.exists(actual_file):
                with open(actual_file, 'rb') as f:
                    buffer.write(f.read())
                
                # Clean up temp file
                os.remove(actual_file)
                
                # Save to our output location
                buffer.seek(0)
                img = Image.open(buffer)
                img.save(filepath)
                print(f"✅ Graphviz diagram saved as: {filename}")
                return filename
            else:
                print(f"❌ Generated file not found: {actual_file}")
                return None
        else:
            print("❌ No graphviz object 'dot' found in code")
            return None
        
    except Exception as e:
        print(f'❌ Graphviz diagram generation error: {e}')
        traceback.print_exc()
        return None

def render_plotly_diagram(code, output_folder):
    """Render plotly diagram"""
    filename = f"plotly_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(output_folder, filename)
    
    try:
        import plotly.graph_objects as go
        import plotly.io as pio
        
        # Create buffer
        buffer = io.BytesIO()
        
        # Prepare execution environment
        exec_globals = {
            'go': go,
            'pio': pio,
            'buffer': buffer
        }
        
        print(f"🔍 Executing plotly code:\n{code}")
        exec(code, exec_globals)
        
        # Save image
        img = Image.open(buffer)
        img.save(filepath)
        print(f"✅ Plotly diagram saved as: {filename}")
        return filename
        
    except Exception as e:
        print(f'❌ Plotly diagram generation error: {e}')
        traceback.print_exc()
        return None

def render_seaborn_diagram(code, output_folder):
    """Render seaborn diagram"""
    filename = f"seaborn_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(output_folder, filename)
    
    try:
        import seaborn as sns
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import pandas as pd
        import numpy as np
        
        # Post-process code for common AI mistakes
        code = code.replace('sns.venn2', '# sns.venn2  # Invalid function, using alternative')
        code = code.replace('sns.venn3', '# sns.venn3  # Invalid function, using alternative')
        
        # Add pandas import if missing
        if 'pd.DataFrame' in code and 'import pandas' not in code:
            code = 'import pandas as pd\n' + code
        
        # Fix common seaborn issues
        if 'sns.venn2(' in code:
            # Replace venn2 with a simple bar plot
            code = code.replace('sns.venn2(', '# sns.venn2(')
            code += '\n# Creating alternative visualization since venn2 is not available'
            code += '\nsns.barplot(data=df, x="Category", y="Value")'
        
        # Create buffer
        buffer = io.BytesIO()
        
        # Prepare execution environment
        exec_globals = {
            'sns': sns,
            'plt': plt,
            'pd': pd,
            'np': np,
            'buffer': buffer
        }
        
        print(f"🔍 Executing seaborn code:\n{code}")
        exec(code, exec_globals)
        
        # Save image
        img = Image.open(buffer)
        img.save(filepath)
        print(f"✅ Seaborn diagram saved as: {filename}")
        return filename
        
    except Exception as e:
        print(f'❌ Seaborn diagram generation error: {e}')
        traceback.print_exc()
        return None

def render_pillow_diagram(code, output_folder):
    """Render pillow diagram"""
    filename = f"pillow_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(output_folder, filename)
    
    try:
        from PIL import Image, ImageDraw
        
        # Create buffer
        buffer = io.BytesIO()
        
        # Prepare execution environment
        exec_globals = {
            'Image': Image,
            'ImageDraw': ImageDraw,
            'buffer': buffer
        }
        
        print(f"🔍 Executing pillow code:\n{code}")
        exec(code, exec_globals)
        
        # Save image
        img = Image.open(buffer)
        img.save(filepath)
        print(f"✅ Pillow diagram saved as: {filename}")
        return filename
        
    except Exception as e:
        print(f'❌ Pillow diagram generation error: {e}')
        traceback.print_exc()
        return None

def render_turtle_diagram(code, output_folder):
    """Render turtle diagram"""
    filename = f"turtle_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(output_folder, filename)
    
    try:
        import turtle
        
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
        img.save(filepath)
        print(f"✅ Turtle diagram saved as: {filename}")
        return filename
        
    except Exception as e:
        print(f'❌ Turtle diagram generation error: {e}')
        traceback.print_exc()
        return None 