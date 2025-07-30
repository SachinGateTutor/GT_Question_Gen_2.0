from graphviz import Source, Digraph
import graphviz
import os
import traceback
import re
import tempfile
import io
import time
import uuid
import ast

def is_python_code(code: str) -> bool:
    """Check if the code is Python code instead of Graphviz code"""
    # Python class indicators (these indicate Python class code, not diagram code)
    python_class_indicators = [
        'class ', 'def __init__', 'self.', 'print(', 'return ',
        'if __name__', 'pass', 'try:', 'except:', 'finally:',
        'with ', 'for ', 'while ', 'lambda ', 'yield ', 'async ', 'await ',
        'raise ', 'assert ', 'del ', 'global ', 'nonlocal ', 'break', 'continue'
    ]
    
    # Graphviz diagram indicators (these indicate proper diagram code)
    graphviz_indicators = [
        'dot = graphviz.digraph()', 'dot.node(', 'dot.edge(', 'dot.render(',
        'graphviz.digraph()', 'dot.attr(', 'dot.subgraph('
    ]
    
    code_lower = code.lower()
    
    # Count Python class indicators
    python_count = sum(1 for indicator in python_class_indicators if indicator in code_lower)
    
    # Count Graphviz indicators
    graphviz_count = sum(1 for indicator in graphviz_indicators if indicator in code_lower)
    
    print(f"🔍 Debug: Python indicators found: {python_count}")
    print(f"🔍 Debug: Graphviz indicators found: {graphviz_count}")
    
    # If we have more Graphviz indicators than Python indicators, it's likely Graphviz code
    if graphviz_count > python_count:
        print(f"🔍 Debug: More Graphviz indicators than Python indicators - likely diagram code")
        return False
    
    # If we have multiple Python class indicators, it's likely Python class code
    if python_count >= 2:
        print(f"🔍 Debug: Multiple Python class indicators found - likely Python class code")
        return True
    
    # If we have at least one Graphviz indicator, it's likely diagram code
    if graphviz_count >= 1:
        print(f"🔍 Debug: Graphviz indicators found - likely diagram code")
        return False
    
    # Default: if no clear indicators, assume it's Python class code if it has class-like patterns
    return python_count >= 1

def render(code: str, output_path: str):
    """Render graphviz diagram with improved error handling and retry mechanism"""
    
    # First: Validate syntax before writing to temp
    try:
        ast.parse(code)
    except SyntaxError as e:
        print(f"❌ Syntax Error in provided graphviz code:\n{e}")
        
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
    
    # Fix common graphviz issues
    code = re.sub(r'style=\'filled\'', 'style="filled"', code)
    code = re.sub(r'fillcolor=\'([^\']+)\'', r'fillcolor="\1"', code)
    code = re.sub(r'color=\'([^\']+)\'', r'color="\1"', code)
    
    # Fix malformed parameter names (common AI mistakes)
    code = re.sub(r'style=\'filled\'', 'style="filled"', code)
    code = re.sub(r'style=\'dashed\'', 'style="dashed"', code)
    code = re.sub(r'style=\'dotted\'', 'style="dotted"', code)
    code = re.sub(r'style=\'bold\'', 'style="bold"', code)
    
    # Fix duplicate style attributes
    code = re.sub(r'style="[^"]*"\s+style="[^"]*"', 'style="filled"', code)
    
    # Remove BytesIO import if present (not needed for file saving)
    code = code.replace('from io import BytesIO', '')
    
    # Fix buffer references - use proper filename only
    filename = os.path.basename(output_path)
    code = code.replace('buffer', f"'{filename}'")
    code = code.replace('dot.render(buffer', f'dot.render("{filename}"')
    
    # Add missing imports if needed
    if 'graphviz' in code and 'import graphviz' not in code:
        code = 'import graphviz\n' + code
    if 'time' in code and 'import time' not in code:
        code = 'import time\n' + code
    if 'uuid' in code and 'import uuid' not in code:
        code = 'import uuid\n' + code
    
    # Save code to temp file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
        temp_path = f.name
        f.write(code)

    # Run the file safely with retry mechanism
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            # Record files before execution - IMPROVED VERSION
            import os
            import glob
            
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
                'graphviz': graphviz,
                'time': time,
                'uuid': uuid,
                'os': os,
                'glob': glob
            }
            exec(code, exec_globals)
            
            # Find newly created PNG files in both locations - IMPROVED VERSION
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
            
            # If no specific patterns found, use any new PNG file
            if not generated_file and new_files:
                generated_file = list(new_files)[0]
                print(f"🔍 Debug: Found newly created PNG file: {generated_file}")
            
            if generated_file:
                # Move the generated file to the output path
                import shutil
                shutil.move(generated_file, output_path)
                print(f"✅ Graphviz diagram saved as: {os.path.basename(output_path)}")
                # Clean up temp file only after successful execution
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return os.path.basename(output_path)
            else:
                print("❌ No graphviz diagram file generated")
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return None
                    
        except Exception as e:
            print(f"❌ Graphviz diagram generation error (attempt {attempt + 1}/{max_retries + 1}): {e}")
            if attempt < max_retries:
                print(f"🔄 Retrying graphviz diagram generation...")
                # Try to fix the code and retry
                try:
                    fixed_code = fix_common_syntax_errors(code)
                    if fixed_code != code:
                        with open(temp_path, 'w', encoding='utf-8') as f:
                            f.write(fixed_code)
                        continue
                except:
                    pass
            else:
                traceback.print_exc()
                # Clean up temp file on final failure
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                return None

def fix_common_syntax_errors(code: str) -> str:
    """Fix common syntax errors in graphviz code"""
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