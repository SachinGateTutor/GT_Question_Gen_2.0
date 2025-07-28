from graphviz import Source, Digraph
import os
import traceback
import re
import tempfile
import io
import time
import uuid

def is_python_code(code: str) -> bool:
    """Check if the code is Python code instead of Graphviz code"""
    python_indicators = [
        'class ',
        'def __init__',
        'self.',
        'print(',
        'import ',
        'from ',
        'if __name__',
        'return ',
        'pass',
        'try:',
        'except:',
        'finally:',
        'with ',
        'for ',
        'while ',
        'lambda ',
        'yield ',
        'async ',
        'await ',
        'raise ',
        'assert ',
        'del ',
        'global ',
        'nonlocal ',
        'break',
        'continue'
    ]
    
    code_lower = code.lower()
    python_count = sum(1 for indicator in python_indicators if indicator in code_lower)
    
    # If more than 2 Python indicators are found, it's likely Python code
    return python_count >= 2

def create_fallback_diagram(output_path: str) -> str:
    """Create a fallback diagram when invalid code is provided"""
    try:
        import graphviz
        
        dot = graphviz.Digraph()
        dot.attr(fontcolor="black")
        dot.attr(edge_color="black")
        
        # Create a simple flowchart
        dot.node('A', 'Start', shape='ellipse', fillcolor="lightgreen", style="filled", fontcolor="black")
        dot.node('B', 'Process', shape='box', fillcolor="lightblue", style="filled", fontcolor="black")
        dot.node('C', 'Decision', shape='diamond', fillcolor="lightyellow", style="filled", fontcolor="black")
        dot.node('D', 'End', shape='octagon', fillcolor="lightcoral", style="filled", fontcolor="black")
        
        dot.edge('A', 'B', label='to process', color="lightcoral", style='dashed')
        dot.edge('B', 'C', label='check', color="lightblue", style='solid')
        dot.edge('C', 'D', label='complete', color="lightgreen", style='bold')
        
        # Save the diagram
        base_path = os.path.splitext(output_path)[0]
        dot.render(base_path, format='png', cleanup=True)
        
        actual_file = base_path + '.png'
        if os.path.exists(actual_file):
            print(f"✅ Fallback diagram created: {os.path.basename(output_path)}")
            return os.path.basename(output_path)
        else:
            print(f"❌ Fallback diagram file not found: {actual_file}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating fallback diagram: {e}")
        return None

def render(code: str, output_path: str):
    """Render graphviz diagram with improved error handling"""
    
    try:
        import graphviz
        import tempfile
        import glob
        import re
        
        # Check if the code is actually Python code instead of Graphviz code
        if is_python_code(code):
            print(f"⚠️ Debug: Detected Python code instead of Graphviz code, creating fallback diagram")
            return create_fallback_diagram(output_path)
        
        # Improve color scheme for better readability
        # Replace dark colors with lighter, more readable alternatives
        color_mappings = {
            'blue': 'lightblue',
            'darkblue': 'lightblue', 
            'navy': 'lightblue',
            'black': 'white',
            'darkgreen': 'lightgreen',
            'green': 'lightgreen',
            'red': 'lightcoral',
            'darkred': 'lightcoral',
            'purple': 'plum',
            'darkpurple': 'plum',
            'brown': 'wheat',
            'darkbrown': 'wheat',
            'gray': 'lightgray',
            'darkgray': 'lightgray',
            'grey': 'lightgray',
            'darkgrey': 'lightgray'
        }
        
        # Apply color mappings for better contrast
        for dark_color, light_color in color_mappings.items():
            code = re.sub(rf'fillcolor=[\'"]{dark_color}[\'"]', f'fillcolor="{light_color}"', code)
            code = re.sub(rf'color=[\'"]{dark_color}[\'"]', f'color="{light_color}"', code)
        
        # Ensure edges are always visible by replacing white/transparent colors
        code = re.sub(r'color=[\'"]white[\'"]', 'color="black"', code)
        code = re.sub(r'color=[\'"]transparent[\'"]', 'color="black"', code)
        code = re.sub(r'color=[\'"]none[\'"]', 'color="black"', code)
        
        # Add font color settings for better readability
        # Ensure text is always dark for good contrast
        # Add fontcolor to all node definitions that have style='filled' (but avoid duplicates)
        code = re.sub(r'style=[\'"]filled[\'"]', 'style="filled", fontcolor="black"', code)
        
        # Fix duplicate style attributes that cause syntax errors
        code = re.sub(r'style=[\'"][^\'"]*[\'"],\s*style=[\'"][^\'"]*[\'"]', 'style="filled"', code)
        code = re.sub(r'style=[\'"][^\'"]*[\'"],\s*style=[\'"][^\'"]*[\'"]', 'style="filled"', code)
        
        # Fix color specifications for graphviz
        # Ensure colors are properly applied to nodes and edges
        code = re.sub(r'fillcolor=[\'"]([^\'"]*)[\'"]', r'fillcolor="\1"', code)
        code = re.sub(r'color=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)
        code = re.sub(r'bgcolor=[\'"]([^\'"]*)[\'"]', r'bgcolor="\1"', code)
        
        # Fix common graphviz color issues
        code = re.sub(r'fc=[\'"]([^\'"]*)[\'"]', r'fillcolor="\1"', code)
        code = re.sub(r'c=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)
        code = re.sub(r'bg=[\'"]([^\'"]*)[\'"]', r'bgcolor="\1"', code)
        
        # Fix invalid colors
        code = re.sub(r'lightpurple', 'plum', code)
        code = re.sub(r'fillcolor="lightpurple"', 'fillcolor="plum"', code)
        
        # Post-process code for common AI mistakes
        # Fix the render method call - graphviz doesn't accept BytesIO directly
        if 'dot.render(buffer, format=' in code:
            code = code.replace('dot.render(buffer, format=\'png\', cleanup=True)', 
                              'dot.render(tempfile.mktemp(), format=\'png\', cleanup=True)')
        
        # Fix dot.edges() calls that have style parameters (not supported by graphviz)
        code = re.sub(r'dot\.edges\(\[([^\]]+)\],\s*style=[\'"][^\'"]+[\'"]', r'dot.edges([\1])', code)
        code = re.sub(r'dot\.edges\(\[([^\]]+)\],\s*color=[\'"][^\'"]+[\'"]', r'dot.edges([\1])', code)
        
        # Create buffer
        buffer = io.BytesIO()
        
        # Prepare execution environment
        exec_globals = {
            'graphviz': graphviz,
            'buffer': buffer,
            'tempfile': tempfile,
            'os': os,
            'time': time,
            'uuid': uuid
        }
        
        # Add global font color setting for better readability
        if 'dot = graphviz.Digraph()' in code:
            code = code.replace('dot = graphviz.Digraph()', 'dot = graphviz.Digraph()\ndot.attr(fontcolor="black")\ndot.attr(edge_color="black")')
        
        print(f"🔍 Executing graphviz code:\n{code}")
        exec(code, exec_globals)
        
        # Graphviz saves to a file, so we need to read it back
        # The dot object should have been created in the code
        dot = exec_globals.get('dot')
        if dot:
            # Save directly to our output location
            base_path = os.path.splitext(output_path)[0]  # Remove .png extension
            dot.render(base_path, format='png', cleanup=True)
            
            # Graphviz creates files with .png extension
            actual_file = base_path + '.png'
            
            # Check if file was created successfully
            if os.path.exists(actual_file):
                print(f"✅ Graphviz diagram saved as: {os.path.basename(output_path)}")
                return os.path.basename(output_path)
            else:
                print(f"❌ Generated file not found: {actual_file}")
                return None
        else:
            print("❌ No graphviz object 'dot' found in code")
            return None
        
    except Exception as e:
        print(f'❌ Graphviz diagram generation error: {e}')
        traceback.print_exc()
        # Try to create a fallback diagram when there's an error
        return create_fallback_diagram(output_path) 