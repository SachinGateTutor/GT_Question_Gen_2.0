from graphviz import Source
import os
import traceback

def render(code: str, output_path: str):
    """Render graphviz diagram with improved error handling"""
    
    try:
        # Post-process code for common AI mistakes
        import re
        
        # Fix color specifications for graphviz
        code = re.sub(r'fillcolor=[\'"]([^\'"]*)[\'"]', r'fillcolor="\1"', code)
        code = re.sub(r'color=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)
        code = re.sub(r'bgcolor=[\'"]([^\'"]*)[\'"]', r'bgcolor="\1"', code)
        
        # Fix common graphviz color issues
        code = re.sub(r'fc=[\'"]([^\'"]*)[\'"]', r'fillcolor="\1"', code)
        code = re.sub(r'c=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)
        code = re.sub(r'bg=[\'"]([^\'"]*)[\'"]', r'bgcolor="\1"', code)
        
        # Fix the render method call - graphviz doesn't accept BytesIO directly
        if 'dot.render(buffer, format=' in code:
            code = code.replace('dot.render(buffer, format=\'png\', cleanup=True)', 
                              'dot.render(tempfile.mktemp(), format=\'png\', cleanup=True)')
        
        src = Source(code)
        src.format = 'png'
        
        # Save directly to our output location
        base_path = os.path.splitext(output_path)[0]  # Remove .png extension
        src.render(filename=base_path, cleanup=True)
        
        # Graphviz creates files with .png extension
        actual_file = base_path + '.png'
        
        # Check if file was created successfully
        if os.path.exists(actual_file):
            print(f"✅ Graphviz diagram saved as: {os.path.basename(output_path)}")
            return os.path.basename(output_path)
        else:
            print(f"❌ Generated file not found: {actual_file}")
            return None
            
    except Exception as e:
        print(f'❌ Graphviz diagram generation error: {e}')
        traceback.print_exc()
        return None 