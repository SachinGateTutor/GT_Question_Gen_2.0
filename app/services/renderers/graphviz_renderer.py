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
        
        # Fix dot.edges() syntax - it should take a list of tuples, not multiple arguments
        code = re.sub(r'dot\.edges\(\[([^\]]+)\], \[([^\]]+)\], \[([^\]]+)\], \[([^\]]+)\], \[([^\]]+)\], \[([^\]]+)\]\)', 
                     r'dot.edges([(\1), (\2), (\3), (\4), (\5), (\6)])', code)
        
        # Fix dot.edges() with multiple arguments
        code = re.sub(r'dot\.edges\(([^)]+)\)', 
                     lambda m: f'dot.edges([{m.group(1)}])' if ',' in m.group(1) else f'dot.edges([{m.group(1)}])', code)
        
        # Fix individual edge calls to use proper syntax
        code = re.sub(r'dot\.edges\(\'([^\']+)\', \'([^\']+)\'\)', r'dot.edge(\1, \2)', code)
        
        # Fix the problematic dot.edges() call from the logs
        # Convert: dot.edges(['10', '5'], ['10', '15'], ['5', '3'], ['5', '7'], ['15', '12'], ['15', '18'])
        # To: dot.edge('10', '5'); dot.edge('10', '15'); etc.
        code = re.sub(r'dot\.edges\(\[([^\]]+)\], \[([^\]]+)\], \[([^\]]+)\], \[([^\]]+)\], \[([^\]]+)\], \[([^\]]+)\]\)', 
                     r'dot.edge(\1)\ndot.edge(\2)\ndot.edge(\3)\ndot.edge(\4)\ndot.edge(\5)\ndot.edge(\6)', code)
        
        # Fix any remaining dot.edges() calls with multiple arguments
        def fix_edges_call(match):
            args = match.group(1)
            # Split by comma and create individual edge calls
            edge_pairs = re.findall(r'\[([^\]]+)\]', args)
            edge_calls = []
            for i in range(0, len(edge_pairs), 2):
                if i + 1 < len(edge_pairs):
                    edge_calls.append(f'dot.edge({edge_pairs[i]}, {edge_pairs[i+1]})')
            return '\n'.join(edge_calls)
        
        code = re.sub(r'dot\.edges\(([^)]+)\)', fix_edges_call, code)
        
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