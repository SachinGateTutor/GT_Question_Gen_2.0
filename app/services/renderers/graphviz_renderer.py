from graphviz import Source, Digraph
import os
import traceback
import re
import tempfile
import io

def render(code: str, output_path: str):
    """Render graphviz diagram with improved error handling"""
    
    try:
        import graphviz
        import tempfile
        import glob
        import re
        
        # Fix color specifications for graphviz
        # Ensure colors are properly applied to nodes and edges
        code = re.sub(r'fillcolor=[\'"]([^\'"]*)[\'"]', r'fillcolor="\1"', code)
        code = re.sub(r'color=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)
        code = re.sub(r'bgcolor=[\'"]([^\'"]*)[\'"]', r'bgcolor="\1"', code)
        
        # Fix common graphviz color issues
        code = re.sub(r'fc=[\'"]([^\'"]*)[\'"]', r'fillcolor="\1"', code)
        code = re.sub(r'c=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)
        code = re.sub(r'bg=[\'"]([^\'"]*)[\'"]', r'bgcolor="\1"', code)
        
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
        return None 