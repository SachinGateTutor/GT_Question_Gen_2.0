import plotly.io as pio
import plotly.graph_objects as go
import os
import traceback
import re
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve
from ..openai_service import ai_correct_diagram_code

def render(code: str, output_path: str):
    """Render plotly diagram with AI-powered self-healing"""
    
    # Apply plotly-specific fixes
    code = apply_plotly_fixes(code, output_path)
    
    # AI-powered self-healing execution with retry mechanism
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            namespace = {'go': go, 'pio': pio}
            
            # Add common imports to namespace
            try:
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
            error_message = str(e)
            print(f"❌ Plotly diagram generation error (attempt {attempt + 1}/{max_retries + 1}): {error_message}")
            
            if attempt < max_retries:
                print(f"🔧 Attempting AI-powered code correction...")
                
                # Try AI-powered error correction
                try:
                    # Extract context from code comments or use defaults
                    subject = "General"
                    topic = "Data Visualization"
                    
                    if '# Subject:' in code:
                        subject = code.split('# Subject:')[1].split('\n')[0].strip()
                    if '# Topic:' in code:
                        topic = code.split('# Topic:')[1].split('\n')[0].strip()
                    
                    corrected_code, correction_success = ai_correct_diagram_code(
                        original_code=code,
                        error_message=error_message,
                        library_name="plotly",
                        subject=subject,
                        topic=topic
                    )
                    
                    if correction_success and corrected_code != code:
                        print(f"✅ AI provided corrected plotly code, attempting execution...")
                        
                        # Apply plotly-specific fixes to corrected code
                        corrected_code = apply_plotly_fixes(corrected_code, output_path)
                        
                        # Update code for next iteration
                        code = corrected_code
                        continue
                    else:
                        print(f"❌ AI correction failed or provided same code")
                        
                except Exception as ai_error:
                    print(f"❌ AI correction failed: {ai_error}")
                
                # Fallback: basic error pattern fixes
                print(f"🔄 Trying basic plotly error fixes...")
                try:
                    fixed_code = fix_common_syntax_errors(code)
                    if fixed_code != code:
                        code = fixed_code
                        continue
                except:
                    pass
            else:
                print(f"❌ All retry attempts failed for plotly diagram generation")
                return None

def apply_plotly_fixes(code, output_path):
    """Apply standard plotly code fixes and transformations"""
    
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
    code = re.sub(r'pio\.write_image\(fig, [\'"][^\'"]*.png[\'"]', f'pio.write_image(fig, "{filename}"', code)
    
    # Add missing imports if needed
    if 'import plotly.graph_objects as go' not in code and 'go.' in code:
        code = 'import plotly.graph_objects as go\n' + code
    if 'import plotly.io as pio' not in code and 'pio.' in code:
        code = 'import plotly.io as pio\n' + code
    if 'import numpy as np' not in code and 'np.' in code:
        code = 'import numpy as np\n' + code
    if 'import pandas as pd' not in code and 'pd.' in code:
        code = 'import pandas as pd\n' + code
    
    return code

def fix_common_syntax_errors(code: str) -> str:
    """Fix common syntax errors in plotly code"""
    
    # Fix missing colons after for loops (only at start of line, not comments)
    code = re.sub(r'^(\s*)for\s+([^:\n#]+)\s*\n(\s*)', r'\1for \2:\n\3', code, flags=re.MULTILINE)
    
    # Fix missing colons after if statements (only at start of line, not comments)
    code = re.sub(r'^(\s*)if\s+([^:\n#]+)\s*\n(\s*)', r'\1if \2:\n\3', code, flags=re.MULTILINE)
    
    # Fix missing colons after while loops (only at start of line, not comments)
    code = re.sub(r'^(\s*)while\s+([^:\n#]+)\s*\n(\s*)', r'\1while \2:\n\3', code, flags=re.MULTILINE)
    
    # Fix missing colons after def statements (only at start of line, not comments)
    code = re.sub(r'^(\s*)def\s+([^:\n#]+)\s*\n(\s*)', r'\1def \2:\n\3', code, flags=re.MULTILINE)
    
    # Fix missing colons after class statements (only at start of line, not comments)
    code = re.sub(r'^(\s*)class\s+([^:\n#]+)\s*\n(\s*)', r'\1class \2:\n\3', code, flags=re.MULTILINE)
    
    # Fix missing colons after for loops (end of line)
    code = re.sub(r'^(\s*)for\s+([^:#]+)\s*$', r'\1for \2:\n\1    pass', code, flags=re.MULTILINE)
    
    # Fix missing colons after if statements (end of line)
    code = re.sub(r'^(\s*)if\s+([^:#]+)\s*$', r'\1if \2:\n\1    pass', code, flags=re.MULTILINE)
    
    # Fix missing colons after while loops (end of line)
    code = re.sub(r'^(\s*)while\s+([^:#]+)\s*$', r'\1while \2:\n\1    pass', code, flags=re.MULTILINE)
    
    # Fix missing colons after def statements (end of line)
    code = re.sub(r'^(\s*)def\s+([^:#]+)\s*$', r'\1def \2:\n\1    pass', code, flags=re.MULTILINE)
    
    # Fix missing colons after class statements (end of line)
    code = re.sub(r'^(\s*)class\s+([^:#]+)\s*$', r'\1class \2:\n\1    pass', code, flags=re.MULTILINE)
    
    # Fix unmatched parentheses by adding missing closing parentheses
    open_parens = code.count('(')
    close_parens = code.count(')')
    if open_parens > close_parens:
        code += ')' * (open_parens - close_parens)
    
    # Fix unmatched brackets by adding missing closing brackets
    open_brackets = code.count('[')
    close_brackets = code.count(']')
    if open_brackets > close_brackets:
        code += ']' * (open_brackets - close_brackets)
    
    # Fix unmatched braces by adding missing closing braces  
    open_braces = code.count('{')
    close_braces = code.count('}')
    if open_braces > close_braces:
        code += '}' * (open_braces - close_braces)
    
    return code 