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
        
        # Fix buffer references - use proper filename only, not full path
        filename = os.path.basename(output_path)
        code = code.replace('buffer', f"'{filename}'")
        code = code.replace('pio.write_image(fig, buffer', f'pio.write_image(fig, "{filename}"')
        
        # Fix hardcoded PNG filenames in pio.write_image() calls
        code = re.sub(r'pio\.write_image\([^,]+,\s*[\'"][^\'"]*.png[\'"]', f'pio.write_image(fig, "{filename}"', code)
        
        # Add missing imports if needed
        if 'np.' in code and 'import numpy' not in code:
            code = 'import numpy as np\n' + code
        if 'pd.' in code and 'import pandas' not in code:
            code = 'import pandas as pd\n' + code
        if 'sklearn.' in code and 'from sklearn' not in code:
            code = 'from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve\n' + code
        
        namespace = {'go': go, 'pio': pio}
        
        # Add common imports to namespace
        try:
            import numpy as np
            import pandas as pd
            from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve
            namespace.update({
                'np': np,
                'pd': pd,
                'confusion_matrix': confusion_matrix,
                'roc_curve': roc_curve,
                'auc': auc,
                'precision_recall_curve': precision_recall_curve
            })
        except ImportError:
            print("⚠️ Warning: Some imports not available")
        
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