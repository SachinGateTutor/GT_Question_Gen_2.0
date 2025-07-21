import tempfile
import runpy
import os
import matplotlib
import ast
import traceback
import io
from PIL import Image

def render(code: str, output_path: str):
    """Render matplotlib diagram with improved error handling"""
    
    matplotlib.use('Agg')  # Use headless backend

    # First: Validate syntax before writing to temp
    try:
        ast.parse(code)
    except SyntaxError as e:
        print(f"❌ Syntax Error in provided matplotlib code:\n{e}")
        return None

    # Post-process code for common AI mistakes
    import re
    
    # Fix color specifications for matplotlib
    code = re.sub(r'color=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)
    code = re.sub(r'facecolor=[\'"]([^\'"]*)[\'"]', r'facecolor="\1"', code)
    code = re.sub(r'edgecolor=[\'"]([^\'"]*)[\'"]', r'edgecolor="\1"', code)
    
    # Fix common matplotlib color issues
    code = re.sub(r'c=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)
    code = re.sub(r'fc=[\'"]([^\'"]*)[\'"]', r'facecolor="\1"', code)
    code = re.sub(r'ec=[\'"]([^\'"]*)[\'"]', r'edgecolor="\1"', code)
    
    # Fix fcolor to facecolor (common AI mistake)
    code = re.sub(r'fcolor=[\'"]([^\'"]*)[\'"]', r'facecolor="\1"', code)
    code = re.sub(r'fcolor=([^\s,)]+)', r'facecolor=\1', code)
    
    # Fix BytesIO references
    code = code.replace('BytesIO()', 'io.BytesIO()')
    code = code.replace('from io import BytesIO', '')
    
    # Fix buffer references
    code = code.replace('buffer', f"'{output_path}'")
    code = code.replace('plt.savefig(buffer', f'plt.savefig("{output_path}"')
    
    # Add missing imports if needed
    if 'np.' in code and 'import numpy' not in code:
        code = 'import numpy as np\n' + code
    if 'pd.' in code and 'import pandas' not in code:
        code = 'import pandas as pd\n' + code
    if 'sklearn.' in code and 'from sklearn' not in code:
        code = 'from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve\n' + code
    
    # Add dummy data for common undefined variables
    if 'y_true' in code and 'y_true =' not in code:
        code = 'y_true = [0, 1, 1, 0, 1, 1, 0]\n' + code
    if 'y_scores' in code and 'y_scores =' not in code:
        code = 'y_scores = [0.2, 0.6, 0.8, 0.3, 0.7, 0.9, 0.1]\n' + code
    if 'y_pred' in code and 'y_pred =' not in code:
        code = 'y_pred = [0, 1, 1, 0, 1, 1, 0]\n' + code
        
    # Fix common matplotlib issues
    if 'plt.show()' in code:
        code = code.replace('plt.show()', '# plt.show()  # Not needed for saving')
    
    # Save code to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        temp_path = f.name
        f.write(code)

    # Check for plt.savefig and inject if not found
    with open(temp_path, 'r+', encoding='utf-8') as f:
        lines = f.readlines()
        new_lines = []
        savefig_found = False

        for line in lines:
            if "plt.savefig" in line:
                savefig_found = True
                new_lines.append(f"plt.savefig(r'{output_path}')\n")
            else:
                new_lines.append(line)

        if not savefig_found:
            new_lines.append("\nimport matplotlib.pyplot as plt\n")
            new_lines.append(f"plt.savefig(r'{output_path}')\n")

        f.seek(0)
        f.writelines(new_lines)
        f.truncate()

    # Run the file safely
    try:
        runpy.run_path(temp_path)
        print(f"✅ Matplotlib diagram saved as: {os.path.basename(output_path)}")
        return os.path.basename(output_path)
    except Exception as e:
        print(f"❌ Matplotlib diagram generation error: {e}")
        traceback.print_exc()
        return None
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path) 