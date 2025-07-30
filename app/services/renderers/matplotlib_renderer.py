import tempfile
import runpy
import os
import matplotlib
import ast
import traceback
import io
from PIL import Image

def render(code: str, output_path: str):
    """Render matplotlib diagram with improved error handling and retry mechanism"""
    
    matplotlib.use('Agg')  # Use headless backend

    # First: Validate syntax before writing to temp
    try:
        ast.parse(code)
    except SyntaxError as e:
        print(f"❌ Syntax Error in provided matplotlib code:\n{e}")
        
        # Try to fix common syntax errors
        fixed_code = fix_common_syntax_errors(code)
        if fixed_code != code:
            try:
                ast.parse(fixed_code)
                print("✅ Fixed syntax errors automatically")
                code = fixed_code
            except SyntaxError:
                print("❌ Could not fix syntax errors automatically")
                return None
        else:
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
    
    # Fix malformed parameter names (common AI mistakes)
    code = re.sub(r'edgedgedgecolor=[\'"]([^\'"]*)[\'"]', r'edgecolor="\1"', code)  # Fix triple "edge" with quotes
    code = re.sub(r'edgedgedgecolor=([^\s,)]+)', r'edgecolor=\1', code)  # Fix triple "edge" without quotes
    code = re.sub(r'edgeedgecolor=[\'"]([^\'"]*)[\'"]', r'edgecolor="\1"', code)    # Fix double "edge" with quotes
    code = re.sub(r'edgeedgecolor=([^\s,)]+)', r'edgecolor=\1', code)    # Fix double "edge" without quotes
    code = re.sub(r'facefacecolor=[\'"]([^\'"]*)[\'"]', r'facecolor="\1"', code)    # Fix double "face" with quotes
    code = re.sub(r'facefacecolor=([^\s,)]+)', r'facecolor=\1', code)    # Fix double "face" without quotes
    code = re.sub(r'colorcolor=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)           # Fix double "color" with quotes
    code = re.sub(r'colorcolor=([^\s,)]+)', r'color=\1', code)           # Fix double "color" without quotes

    # Fix face+edge parameter combinations that cause errors (AGGRESSIVE FIXING)
    # Fix all variations of facedgedgecolor
    code = re.sub(r'facedgedgecolor\s*=\s*[\'"]([^\'"]*)[\'"]', r'facecolor="\1"', code)  
    code = re.sub(r'facedgedgecolor\s*=\s*([^\s,)]+)', r'facecolor=\1', code)
    # Fix all variations of faceedgecolor  
    code = re.sub(r'faceedgecolor\s*=\s*[\'"]([^\'"]*)[\'"]', r'facecolor="\1"', code)
    code = re.sub(r'faceedgecolor\s*=\s*([^\s,)]+)', r'facecolor=\1', code)
    # Fix all variations of edgefacecolor
    code = re.sub(r'edgefacecolor\s*=\s*[\'"]([^\'"]*)[\'"]', r'edgecolor="\1"', code)
    code = re.sub(r'edgefacecolor\s*=\s*([^\s,)]+)', r'edgecolor=\1', code)
    # Fix any other malformed combinations
    code = re.sub(r'edgedgedgecolor\s*=\s*[\'"]([^\'"]*)[\'"]', r'edgecolor="\1"', code)
    code = re.sub(r'edgedgedgecolor\s*=\s*([^\s,)]+)', r'edgecolor=\1', code)
    
    # Fix invalid matplotlib parameters
    code = re.sub(r'ecolor=[\'"]([^\'"]*)[\'"]', r'edgecolor="\1"', code)
    code = re.sub(r'ecolor=([^\s,)]+)', r'edgecolor=\1', code)
    
    # More comprehensive arrow parameter fixes
    code = re.sub(r'plt\.arrow\([^)]*edgedgecolor=[^)]*\)', 'plt.arrow(0.45, 0.5, 0.1, 0, head_width=0.05, head_length=0.05)', code)
    code = re.sub(r'plt\.arrow\([^)]*edgedgedgecolor=[^)]*\)', 'plt.arrow(0.45, 0.5, 0.1, 0, head_width=0.05, head_length=0.05)', code)
    code = re.sub(r'ax\.arrow\([^)]*edgedgecolor=[^)]*\)', 'ax.arrow(0.45, 0.5, 0.1, 0, head_width=0.05, head_length=0.05)', code)
    code = re.sub(r'ax\.arrow\([^)]*edgedgedgecolor=[^)]*\)', 'ax.arrow(0.45, 0.5, 0.1, 0, head_width=0.05, head_length=0.05)', code)
    
    # Remove problematic arrow parameters that cause errors
    # Replace problematic arrow calls with simpler versions
    code = re.sub(r'ax\.arrow\([^)]*ecolor=[^)]*\)', 'ax.arrow(0.45, 0.5, 0.1, 0, head_width=0.05, head_length=0.05)', code)
    code = re.sub(r'ax\.arrow\([^)]*facecolor=[^)]*\)', 'ax.arrow(0.45, 0.5, 0.1, 0, head_width=0.05, head_length=0.05)', code)
    
    # Fix fcolor to facecolor (common AI mistake)
    code = re.sub(r'fcolor=[\'"]([^\'"]*)[\'"]', r'facecolor="\1"', code)
    code = re.sub(r'fcolor=([^\s,)]+)', r'facecolor=\1', code)
    
    # Remove BytesIO import if present (not needed for file saving)
    code = code.replace('from io import BytesIO', '')
    
    # Fix buffer references - use proper filename only
    filename = os.path.basename(output_path)
    code = code.replace('buffer', f"'{filename}'")
    code = code.replace('plt.savefig(buffer', f'plt.savefig("{filename}"')
    
    # Fix hardcoded PNG filenames in plt.savefig() calls
    import re
    # Replace any hardcoded .png filename in plt.savefig() with our proper filename
    code = re.sub(r'plt\.savefig\([\'"][^\'"]*.png[\'"]', f'plt.savefig("{filename}"', code)
    
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
        
    # Add safeguard to prevent path corruption in code
    with open(temp_path, 'r', encoding='utf-8') as f:
        temp_content = f.read()
    
    # Fix any accidental path insertions that might corrupt the code
    temp_content = re.sub(r"'[^']*matplotlib_[^']*\.png'(?=\w)", '', temp_content)  # Remove stray paths
    temp_content = re.sub(r'"[^"]*matplotlib_[^"]*\.png"(?=\w)', '', temp_content)  # Remove stray paths
    
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(temp_content)

    # Apply malformed parameter fixes AFTER plt.savefig check
    with open(temp_path, 'r', encoding='utf-8') as f:
        code = f.read()
    
    # Final safety check: Remove any remaining problematic patterns
    code = re.sub(r'bbox\s*=\s*dict\([^)]*facedg[^)]*\)', 'bbox=dict(facecolor="white", edgecolor="black")', code)
    code = re.sub(r'bbox\s*=\s*dict\([^)]*edgeface[^)]*\)', 'bbox=dict(facecolor="white", edgecolor="black")', code)
    
    # Fix malformed parameter names (common AI mistakes)
    code = re.sub(r'edgedgedgecolor=[\'"]([^\'"]*)[\'"]', r'edgecolor="\1"', code)  # Fix triple "edge" with quotes
    code = re.sub(r'edgedgedgecolor=([^\s,)]+)', r'edgecolor=\1', code)  # Fix triple "edge" without quotes
    code = re.sub(r'edgeedgecolor=[\'"]([^\'"]*)[\'"]', r'edgecolor="\1"', code)    # Fix double "edge" with quotes
    code = re.sub(r'edgeedgecolor=([^\s,)]+)', r'edgecolor=\1', code)    # Fix double "edge" without quotes
    code = re.sub(r'facefacecolor=[\'"]([^\'"]*)[\'"]', r'facecolor="\1"', code)    # Fix double "face" with quotes
    code = re.sub(r'facefacecolor=([^\s,)]+)', r'facecolor=\1', code)    # Fix double "face" without quotes
    code = re.sub(r'colorcolor=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)           # Fix double "color" with quotes
    code = re.sub(r'colorcolor=([^\s,)]+)', r'color=\1', code)           # Fix double "color" without quotes

    # Fix face+edge parameter combinations that cause errors (second pass)
    code = re.sub(r'facedgedgecolor=', 'facecolor=', code)  # Fix facedgedgecolor
    code = re.sub(r'faceedgecolor=', 'facecolor=', code)    # Fix faceedgecolor
    code = re.sub(r'edgefacecolor=', 'edgecolor=', code)    # Fix edgefacecolor
    
    # Write the fixed code back
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(code)

    # Run the file safely with retry mechanism
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            runpy.run_path(temp_path)
            
            # Check if the file was actually created
            if os.path.exists(output_path):
                print(f"✅ Matplotlib diagram saved as: {os.path.basename(output_path)}")
                # Clean up temp file only after successful execution
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return os.path.basename(output_path)
            else:
                # Look for any newly created PNG files
                import glob
                # IMPROVED VERSION: Check both current and output directories
                output_dir = os.path.dirname(output_path) if output_path else ""
                current_dir = os.getcwd()
                
                print(f"🔍 Debug: Searching for PNG files in current dir: {current_dir}")
                png_files_current = glob.glob("*.png")
                png_files_output = []
                
                # Safely check output directory if it exists and is different
                if output_dir and os.path.exists(output_dir) and os.path.abspath(output_dir) != os.path.abspath(current_dir):
                    try:
                        print(f"🔍 Debug: Searching for PNG files in output dir: {output_dir}")
                        png_files_output = glob.glob(os.path.join(output_dir, "*.png"))
                    except Exception as e:
                        print(f"⚠️ Warning: Could not scan output directory {output_dir}: {e}")
                        png_files_output = []
                
                png_files = png_files_current + [os.path.basename(f) for f in png_files_output]
                print(f"🔍 Debug: Found PNG files: current={len(png_files_current)}, output={len(png_files_output)}")
                if png_files:
                    # Move the first PNG file found to the output path
                    import shutil
                    source_file = png_files[0]
                    shutil.move(source_file, output_path)
                    print(f"✅ Matplotlib diagram found and moved: {os.path.basename(output_path)}")
                    # Clean up temp file only after successful execution
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    return os.path.basename(output_path)
                else:
                    print("❌ No matplotlib diagram file generated")
                    # Clean up temp file
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    return None
                    
        except Exception as e:
            error_message = str(e)
            print(f"❌ Matplotlib diagram generation error (attempt {attempt + 1}/{max_retries + 1}): {error_message}")
            
            if attempt < max_retries:
                print(f"🔧 Attempting AI-powered code correction...")
                
                # Try AI-powered error correction
                try:
                    from ..openai_service import ai_correct_diagram_code
                    
                    # Extract subject and topic from the code context (simple heuristic)
                    subject = "General"  # Default
                    topic = "Data Visualization"  # Default
                    
                    # Try to extract more context from code comments
                    if '# Subject:' in code:
                        subject = code.split('# Subject:')[1].split('\n')[0].strip()
                    if '# Topic:' in code:
                        topic = code.split('# Topic:')[1].split('\n')[0].strip()
                    
                    corrected_code, correction_success = ai_correct_diagram_code(
                        original_code=code,
                        error_message=error_message,
                        library_name="matplotlib",
                        subject=subject,
                        topic=topic
                    )
                    
                    if correction_success and corrected_code != code:
                        print(f"✅ AI provided corrected code, attempting execution...")
                        
                        # Apply our standard fixes to the corrected code
                        corrected_code = apply_matplotlib_fixes(corrected_code, output_path)
                        
                        # Write corrected code to temp file
                        with open(temp_path, 'w', encoding='utf-8') as f:
                            f.write(corrected_code)
                        
                        # Update code variable for next iteration
                        code = corrected_code
                        continue
                    else:
                        print(f"❌ AI correction failed or provided same code, trying standard fixes...")
                        
                except Exception as ai_error:
                    print(f"❌ AI correction failed: {ai_error}")
                
                # Fallback to standard syntax error fixes
                print(f"🔄 Trying standard syntax error fixes...")
                try:
                    fixed_code = fix_common_syntax_errors(code)
                    if fixed_code != code:
                        with open(temp_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_code)
                        code = fixed_code
                        continue
                except:
                    pass
            else:
                print(f"❌ All retry attempts failed for matplotlib diagram generation")
                traceback.print_exc()
                # Clean up temp file on final failure
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return None

def fix_common_syntax_errors(code: str) -> str:
    """Fix common syntax errors in matplotlib code"""
    import re
    
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

def apply_matplotlib_fixes(code, output_path):
    """Apply standard matplotlib code fixes and transformations"""
    import re
    import os
    
    # Remove BytesIO import if present (not needed for file saving)
    code = code.replace('from io import BytesIO', '')
    
    # Fix buffer references - use proper filename only
    filename = os.path.basename(output_path)
    code = code.replace('buffer', f"'{filename}'")
    code = code.replace('plt.savefig(buffer', f'plt.savefig("{filename}"')
    
    # Fix hardcoded PNG filenames in plt.savefig() calls
    # Replace any hardcoded .png filename in plt.savefig() with our proper filename
    code = re.sub(r'plt\.savefig\([\'"][^\'"]*.png[\'"]', f'plt.savefig("{filename}"', code)
    
    # Add missing imports if needed
    if 'import matplotlib.pyplot as plt' not in code and 'plt.' in code:
        code = 'import matplotlib.pyplot as plt\n' + code
    if 'import numpy as np' not in code and 'np.' in code:
        code = 'import numpy as np\n' + code
    
    # Fix numpy factorial issue
    if 'np.factorial' in code:
        if 'from scipy.special import factorial' not in code:
            code = 'from scipy.special import factorial\n' + code
        code = code.replace('np.factorial', 'factorial')
    
    # Fix deprecated seaborn style
    code = code.replace("plt.style.use('seaborn')", "plt.style.use('seaborn-v0_8')")
    
    return code 
