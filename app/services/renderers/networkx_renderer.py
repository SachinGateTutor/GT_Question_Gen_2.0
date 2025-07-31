import matplotlib.pyplot as plt
import networkx as nx
import os
import traceback
import re
import tempfile
import glob
import shutil
from ..openai_service import ai_correct_diagram_code

def is_python_code(code: str) -> bool:
    """Check if the provided string is valid Python code."""
    try:
        compile(code, "<string>", "exec")
        return True
    except SyntaxError:
        return False

def render(code: str, output_path: str):
    """Render diagram using networkx"""
    
    if not is_python_code(code):
        print(f"❌ Debug: Code is not Python code, skipping networkx rendering")
        return None

    print(f"🔍 Debug: Rendering networkx diagram...")
    
    # Apply networkx-specific fixes
    code = apply_networkx_fixes(code, output_path)
    
    # Save code to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        temp_path = f.name
        f.write(code)

    # AI-powered self-healing execution with retry mechanism
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            # Record files before execution
            
            # Get the output directory for proper file tracking
            output_dir = os.path.dirname(output_path) if output_path else ""
            current_dir = os.getcwd()
            
            print(f"🔍 Debug: Current working directory: {current_dir}")
            print(f"🔍 Debug: Output directory: {output_dir}")
            
            # Record PNG files in both current directory and output directory
            files_before_current = set(glob.glob("*.png"))
            files_before_output = set()
            
            # Safely check output directory if it exists and is different from current
            if output_dir and os.path.exists(output_dir) and os.path.abspath(output_dir) != os.path.abspath(current_dir):
                try:
                    files_before_output = set(glob.glob(os.path.join(output_dir, "*.png")))
                except Exception as e:
                    print(f"⚠️ Warning: Could not scan output directory {output_dir}: {e}")
                    files_before_output = set()
            
            print(f"🔍 Debug: PNG files in current dir before: {len(files_before_current)}")
            print(f"🔍 Debug: PNG files in output dir before: {len(files_before_output)}")
            
            # Execute the diagram code
            exec_globals = {
                'nx': nx,
                'plt': plt,
                'os': os,
                'glob': glob
            }
            exec(code, exec_globals)
            
            # Find newly created PNG files in both locations
            files_after_current = set(glob.glob("*.png"))
            files_after_output = set()
            
            # Safely check output directory again
            if output_dir and os.path.exists(output_dir) and os.path.abspath(output_dir) != os.path.abspath(current_dir):
                try:
                    files_after_output = set(glob.glob(os.path.join(output_dir, "*.png")))
                except Exception as e:
                    print(f"⚠️ Warning: Could not scan output directory {output_dir} after execution: {e}")
                    files_after_output = set()
            
            new_files_current = files_after_current - files_before_current
            new_files_output = files_after_output - files_before_output
            new_files = new_files_current.union(new_files_output)
            
            print(f"🔍 Debug: New PNG files in current dir: {new_files_current}")
            print(f"🔍 Debug: New PNG files in output dir: {new_files_output}")
            print(f"🔍 Debug: All new PNG files: {new_files}")
            
            # Look for the generated file - prioritize specific patterns first, then any new PNG
            possible_files = [
                "temp.png",
                "temp",
                "test.png", 
                "test"
            ]
            
            generated_file = None
            
            # First check specific patterns
            for file in possible_files:
                if os.path.exists(file):
                    generated_file = file
                    break
                elif os.path.exists(file + ".png"):
                    generated_file = file + ".png"
                    break
            
            # If no specific pattern found, use the first new PNG file
            if not generated_file and new_files:
                generated_file = list(new_files)[0]
            
            # If still no file found, check for any PNG file with networkx pattern
            if not generated_file:
                all_png_files = list(files_after_current) + list(files_after_output)
                for file in all_png_files:
                    if 'networkx' in file.lower() or 'temp' in file.lower() or 'test' in file.lower():
                        generated_file = file
                        break
            
            if generated_file:
                # Move the file to the output path
                if os.path.exists(generated_file):
                    shutil.move(generated_file, output_path)
                print(f"✅ Networkx diagram saved as: {os.path.basename(output_path)}")
                # Clean up temp file only after successful execution
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return os.path.basename(output_path)
            else:
                print(f"❌ Debug: Generated file {generated_file} not found")
                print(f"❌ Debug: No networkx diagram file generated")
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return None
                    
        except Exception as e:
            error_message = str(e)
            print(f"❌ Networkx diagram generation error (attempt {attempt + 1}/{max_retries + 1}): {error_message}")
            
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
                        library_name="networkx",
                        subject=subject,
                        topic=topic
                    )
                    
                    if correction_success and corrected_code != code:
                        print(f"✅ AI provided corrected networkx code, attempting execution...")
                        
                        # Apply networkx-specific fixes to corrected code
                        corrected_code = apply_networkx_fixes(corrected_code, output_path)
                        
                        # Update code for next iteration
                        code = corrected_code
                        continue
                    else:
                        print(f"❌ AI correction failed or provided same code")
                        
                except Exception as ai_error:
                    print(f"❌ AI correction failed: {ai_error}")
                
                # Fallback: basic error pattern fixes
                print(f"🔄 Trying basic networkx error fixes...")
                try:
                    fixed_code = fix_common_syntax_errors(code)
                    if fixed_code != code:
                        code = fixed_code
                        continue
                except:
                    pass
            else:
                print(f"❌ All retry attempts failed for networkx diagram generation")
                return None

def apply_networkx_fixes(code, output_path):
    """Apply standard networkx code fixes and transformations"""
    
    # Fix color specifications for networkx
    code = re.sub(r'node_color=[\'"]([^\'"]*)[\'"]', r'node_color="\1"', code)
    code = re.sub(r'edge_color=[\'"]([^\'"]*)[\'"]', r'edge_color="\1"', code)
    code = re.sub(r'color=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)
    
    # Fix common networkx color issues
    code = re.sub(r'nc=[\'"]([^\'"]*)[\'"]', r'node_color="\1"', code)
    code = re.sub(r'ec=[\'"]([^\'"]*)[\'"]', r'edge_color="\1"', code)
    
    # Fix buffer references - use proper filename only, not full path
    filename = os.path.basename(output_path)
    code = code.replace('plt.savefig(buffer', f'plt.savefig("{filename}"')
    
    # Fix hardcoded PNG filenames in plt.savefig() calls
    code = re.sub(r'plt\.savefig\([\'"][^\'"]*.png[\'"]', f'plt.savefig("{filename}"', code)
    
    # Add missing imports if needed
    if 'import networkx as nx' not in code and 'nx.' in code:
        code = 'import networkx as nx\n' + code
    if 'import matplotlib.pyplot as plt' not in code and 'plt.' in code:
        code = 'import matplotlib.pyplot as plt\n' + code
    
    return code

def fix_common_syntax_errors(code: str) -> str:
    """Fix common syntax errors in networkx code"""
    
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