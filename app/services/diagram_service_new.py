import os
import uuid
from PIL import Image
import io
import sys
import traceback
import subprocess
import tempfile
import shutil
import re

# Import the new modular renderers
from .renderers import (
    plantuml_renderer,
    graphviz_renderer, 
    schemdraw_renderer,
    matplotlib_renderer,
    networkx_renderer,
    plotly_renderer,
    seaborn_renderer,
    pillow_renderer,
    turtle_renderer
)

def detect_diagram_type(code):
    """Detect diagram type using pattern matching (simplified version of diagram_renderer's ML approach)"""
    code_lower = code.lower()
    
    # PlantUML patterns
    if any(pattern in code_lower for pattern in ['@startuml', 'plantuml', 'uml']):
        return 'plantuml'
    
    # Existing library patterns
    if 'schemdraw' in code_lower or 'drawing()' in code_lower:
        return 'schemdraw'
    elif 'matplotlib' in code_lower or 'plt.' in code_lower:
        return 'matplotlib'
    elif 'networkx' in code_lower or 'nx.' in code_lower:
        return 'networkx'
    elif 'graphviz' in code_lower or 'dot.' in code_lower or 'digraph' in code_lower:
        return 'graphviz'
    elif 'plotly' in code_lower or 'go.' in code_lower:
        return 'plotly'
    elif 'seaborn' in code_lower or 'sns.' in code_lower:
        return 'seaborn'
    elif 'pil' in code_lower or 'imagedraw' in code_lower:
        return 'pillow'
    elif 'turtle' in code_lower:
        return 'turtle'
    
    # Default fallback
    return 'schemdraw'

def render_diagram(code, library_name=None, output_folder=None):
    """Render diagram using the specified library with automatic detection"""
    
    # Ensure the output directory exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Auto-detect library if not specified
    if library_name is None:
        library_name = detect_diagram_type(code)
        print(f"🔍 Auto-detected diagram type: {library_name}")
    
    filename = f"{library_name}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(output_folder, filename)
    
    try:
        # Use the modular renderer approach
        if library_name == 'plantuml':
            return plantuml_renderer.render(code, filepath)
        elif library_name == 'schemdraw':
            return schemdraw_renderer.render(code, filepath)
        elif library_name == 'matplotlib':
            return matplotlib_renderer.render(code, filepath)
        elif library_name == 'networkx':
            return networkx_renderer.render(code, filepath)
        elif library_name == 'graphviz':
            return graphviz_renderer.render(code, filepath)
        elif library_name == 'plotly':
            return plotly_renderer.render(code, filepath)
        elif library_name == 'seaborn':
            return seaborn_renderer.render(code, filepath)
        elif library_name == 'pillow':
            return pillow_renderer.render(code, filepath)
        elif library_name == 'turtle':
            return turtle_renderer.render(code, filepath)
        else:
            print(f"❌ Unknown library: {library_name}, falling back to schemdraw")
            return schemdraw_renderer.render(code, filepath)
            
    except Exception as e:
        print(f'❌ Diagram generation error for {library_name}: {e}')
        traceback.print_exc()
        return None

# Backward compatibility - keep the old function name
def render_diagram_old(code, library_name, output_folder):
    """Legacy function for backward compatibility"""
    return render_diagram(code, library_name, output_folder) 