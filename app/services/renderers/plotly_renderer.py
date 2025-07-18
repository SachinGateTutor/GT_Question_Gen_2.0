import plotly.io as pio
import plotly.graph_objects as go
import os
import traceback
import re

def render(code: str, output_path: str):
    """Render plotly diagram with improved error handling"""
    
    try:
        # Post-process code for common AI mistakes
        # Fix color specifications for plotly
        code = re.sub(r'color=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)
        code = re.sub(r'colorscale=[\'"]([^\'"]*)[\'"]', r'colorscale="\1"', code)
        code = re.sub(r'line_color=[\'"]([^\'"]*)[\'"]', r'line_color="\1"', code)
        
        # Fix common plotly color issues
        code = re.sub(r'c=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)
        code = re.sub(r'cs=[\'"]([^\'"]*)[\'"]', r'colorscale="\1"', code)
        code = re.sub(r'lc=[\'"]([^\'"]*)[\'"]', r'line_color="\1"', code)
        
        namespace = {'go': go, 'pio': pio}
        exec(code, namespace)
        fig = namespace.get("fig")
        if fig:
            pio.write_image(fig, output_path)
            print(f"✅ Plotly diagram saved as: {os.path.basename(output_path)}")
            return os.path.basename(output_path)
        else:
            print("❌ No figure object 'fig' found in plotly code")
            return None
            
    except Exception as e:
        print(f'❌ Plotly diagram generation error: {e}')
        traceback.print_exc()
        return None 