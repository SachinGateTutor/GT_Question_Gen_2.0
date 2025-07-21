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
        
        # Fix buffer references - use raw strings to avoid unicode issues
        code = code.replace('buffer', f"r'{output_path}'")
        code = code.replace('plt.savefig(buffer', f'plt.savefig(r"{output_path}"')
        
        # Fix lineplot syntax issues
        code = re.sub(r'sns\.lineplot\(([^,]+),\s*([^,]+)', r'sns.lineplot(x=\1, y=\2', code)
        
        # Fix double x= and y= parameters that might be created by the regex
        code = re.sub(r'x=x=', 'x=', code)
        code = re.sub(r'y=y=', 'y=', code)
        
        # Fix deprecated sklearn imports
        code = code.replace('from sklearn.metrics import plot_confusion_matrix', '# from sklearn.metrics import plot_confusion_matrix  # Deprecated')
        
        # Fix cmapalette typo
        code = code.replace('cmapalette', 'cmap')
        
        # Fix RocCurveDisplay issues
        code = code.replace('RocCurveDisplay(fpr=fpr, tpr=tpr).plot()', 'plt.plot(fpr, tpr)')
        
        # Post-process code for common AI mistakes
        code = code.replace('sns.venn2', '# sns.venn2  # Invalid function, using alternative')
        code = code.replace('sns.venn3', '# sns.venn3  # Invalid function, using alternative')
        
        # Add pandas import if missing
        if 'pd.DataFrame' in code and 'import pandas' not in code:
            code = 'import pandas as pd\n' + code
        
        # Add numpy import if missing
        if 'np.' in code and 'import numpy' not in code:
            code = 'import numpy as np\n' + code
        
        # Add sklearn imports if missing
        if 'sklearn.' in code and 'from sklearn' not in code:
            code = 'from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve\n' + code
        
        # Add dummy data for common undefined variables
        if 'y_true' in code and 'y_true =' not in code:
            code = 'y_true = [0, 1, 1, 0, 1, 1, 0]\n' + code
        if 'y_scores' in code and 'y_scores =' not in code:
            code = 'y_scores = [0.2, 0.6, 0.8, 0.3, 0.7, 0.9, 0.1]\n' + code
        if 'y_pred' in code and 'y_pred =' not in code:
            code = 'y_pred = [0, 1, 1, 0, 1, 1, 0]\n' + code
        
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
        
        # Add sklearn imports to globals - handle each import separately
        try:
            from sklearn.metrics import confusion_matrix
            exec_globals['confusion_matrix'] = confusion_matrix
        except ImportError:
            def dummy_confusion_matrix(*args, **kwargs):
                return [[1, 0], [0, 1]]
            exec_globals['confusion_matrix'] = dummy_confusion_matrix
        
        try:
            from sklearn.metrics import roc_curve
            exec_globals['roc_curve'] = roc_curve
        except ImportError:
            def dummy_roc_curve(*args, **kwargs):
                return [0, 1], [0, 1], [0, 1]
            exec_globals['roc_curve'] = dummy_roc_curve
        
        try:
            from sklearn.metrics import auc
            exec_globals['auc'] = auc
        except ImportError:
            def dummy_auc(*args, **kwargs):
                return 0.5
            exec_globals['auc'] = dummy_auc
        
        try:
            from sklearn.metrics import precision_recall_curve
            exec_globals['precision_recall_curve'] = precision_recall_curve
        except ImportError:
            def dummy_precision_recall_curve(*args, **kwargs):
                return [1, 0], [1, 0], [0, 1]
            exec_globals['precision_recall_curve'] = dummy_precision_recall_curve
        
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