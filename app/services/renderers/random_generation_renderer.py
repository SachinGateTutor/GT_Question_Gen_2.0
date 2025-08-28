import os
import uuid
import traceback
from PIL import Image
import io
import sys
import subprocess
import tempfile
import shutil
import re

# Import the existing renderers
from . import (
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
    """Detect diagram type using pattern matching"""
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

def render_diagram_for_random(code, library_name=None, output_folder=None):
    """Render diagram specifically for random generation service"""
    
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
            result = plantuml_renderer.render(code, filepath)
        elif library_name == 'schemdraw':
            result = schemdraw_renderer.render(code, filepath)
        elif library_name == 'matplotlib':
            result = matplotlib_renderer.render(code, filepath)
        elif library_name == 'networkx':
            result = networkx_renderer.render(code, filepath)
        elif library_name == 'graphviz':
            result = graphviz_renderer.render(code, filepath)
        elif library_name == 'plotly':
            result = plotly_renderer.render(code, filepath)
        elif library_name == 'seaborn':
            result = seaborn_renderer.render(code, filepath)
        elif library_name == 'pillow':
            result = pillow_renderer.render(code, filepath)
        elif library_name == 'turtle':
            result = turtle_renderer.render(code, filepath)
        else:
            print(f"❌ Unknown library: {library_name}, falling back to schemdraw")
            result = schemdraw_renderer.render(code, filepath)
        
        # Handle the result - it could be a string (filename) or dict
        if isinstance(result, str):
            # It's a filename, create the full URL path
            image_url = f"/static/images/{result}"
            print(f"✅ Diagram rendered successfully: {image_url}")
            return {
                'success': True,
                'image_url': image_url,
                'filename': result
            }
        elif isinstance(result, dict):
            # It's already a dictionary, return as is
            return result
        else:
            print(f"❌ Unexpected result type: {type(result)}")
            return {
                'success': False,
                'image_url': None,
                'error': 'Unexpected result type'
            }
            
    except Exception as e:
        print(f'❌ Diagram generation error for {library_name}: {e}')
        traceback.print_exc()
        return {
            'success': False,
            'image_url': None,
            'error': str(e)
        }

def render_option_diagram_for_random(code, library_name, output_folder):
    """Render option diagram specifically for random generation service"""
    return render_diagram_for_random(code, library_name, output_folder) 