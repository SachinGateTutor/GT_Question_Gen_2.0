import matplotlib.pyplot as plt
import networkx as nx
import os
import traceback
import re

def render(code: str, output_path: str):
    """Render networkx diagram with improved error handling"""
    
    try:
        # Post-process code for common AI mistakes
        # Fix color specifications for networkx
        code = re.sub(r'node_color=[\'"]([^\'"]*)[\'"]', r'node_color="\1"', code)
        code = re.sub(r'edge_color=[\'"]([^\'"]*)[\'"]', r'edge_color="\1"', code)
        code = re.sub(r'color=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)
        
        # Fix common networkx color issues
        code = re.sub(r'nc=[\'"]([^\'"]*)[\'"]', r'node_color="\1"', code)
        code = re.sub(r'ec=[\'"]([^\'"]*)[\'"]', r'edge_color="\1"', code)
        
        # Fix buffer references - use proper filename only, not full path
        filename = os.path.basename(output_path)
        code = code.replace('buffer', f"'{filename}'")
        code = code.replace('plt.savefig(buffer', f'plt.savefig("{filename}"')
        
        # Fix hardcoded PNG filenames in plt.savefig() calls
        code = re.sub(r'plt\.savefig\([\'"][^\'"]*.png[\'"]', f'plt.savefig("{filename}"', code)
        
        plt.clf()
        namespace = {'nx': nx, 'plt': plt}
        exec(code, namespace)
        plt.savefig(output_path)
        print(f"✅ Networkx diagram saved as: {os.path.basename(output_path)}")
        return os.path.basename(output_path)
        
    except Exception as e:
        print(f'❌ Networkx diagram generation error: {e}')
        traceback.print_exc()
        return None 