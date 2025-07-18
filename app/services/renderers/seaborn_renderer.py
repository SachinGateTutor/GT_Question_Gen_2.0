import seaborn as sns
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os
import traceback
import re
import io
from PIL import Image

def render(code: str, output_path: str):
    """Render seaborn diagram with improved error handling"""
    
    try:
        # Post-process code for common AI mistakes
        # Fix color specifications for seaborn
        code = re.sub(r'color=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)
        code = re.sub(r'palette=[\'"]([^\'"]*)[\'"]', r'palette="\1"', code)
        code = re.sub(r'hue=[\'"]([^\'"]*)[\'"]', r'hue="\1"', code)
        
        # Fix common seaborn color issues
        code = re.sub(r'c=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)
        code = re.sub(r'p=[\'"]([^\'"]*)[\'"]', r'palette="\1"', code)
        
        # Post-process code for common AI mistakes
        code = code.replace('sns.venn2', '# sns.venn2  # Invalid function, using alternative')
        code = code.replace('sns.venn3', '# sns.venn3  # Invalid function, using alternative')
        
        # Add pandas import if missing
        if 'pd.DataFrame' in code and 'import pandas' not in code:
            code = 'import pandas as pd\n' + code
        
        # Fix common seaborn issues
        if 'sns.venn2(' in code:
            # Replace venn2 with a simple bar plot
            code = code.replace('sns.venn2(', '# sns.venn2(')
            code += '\n# Creating alternative visualization since venn2 is not available'
            code += '\nsns.barplot(data=df, x="Category", y="Value")'
        
        # Prepare execution environment
        exec_globals = {
            'sns': sns,
            'plt': plt,
            'pd': pd,
            'np': np
        }
        
        print(f"🔍 Executing seaborn code:\n{code}")
        exec(code, exec_globals)
        
        # Save image directly to output path
        plt.savefig(output_path, bbox_inches='tight', dpi=300)
        plt.close()  # Close the figure to free memory
        print(f"✅ Seaborn diagram saved as: {os.path.basename(output_path)}")
        return os.path.basename(output_path)
        
    except Exception as e:
        print(f'❌ Seaborn diagram generation error: {e}')
        traceback.print_exc()
        return None 