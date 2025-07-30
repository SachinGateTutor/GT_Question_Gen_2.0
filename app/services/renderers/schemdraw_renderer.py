import schemdraw
import schemdraw.elements as elm
import schemdraw.logic as logic
import matplotlib
matplotlib.use('Agg')
import io
import traceback
import re
import os

def render(code: str, output_path: str):
    """Render schemdraw diagram with AI-powered self-healing"""
    
    # Apply schemdraw-specific fixes
    code = apply_schemdraw_fixes(code, output_path)
    
    # AI-powered self-healing execution with retry mechanism
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            # Post-process code for common AI mistakes (keeping the good parts from current system)
            code = code.replace('SchemDraw', 'schemdraw')
            
            # Check if code uses 'e.' elements before replacing the import
            uses_elements = re.search(r'\be\.\w+', code)
            
            # Only replace elements import if code doesn't use 'e.' elements
            if not uses_elements:
                code = code.replace('import schemdraw.elements as e', 'import schemdraw.logic as logic')
                code = code.replace('import SchemDraw.elements as e', 'import schemdraw.logic as logic')
            # Otherwise, keep the elements import but fix the library name
            else:
                code = code.replace('import SchemDraw.elements as e', 'import schemdraw.elements as e')
            
            code = code.replace('import schemdraw as schem', 'import schemdraw')
            code = code.replace('import SchemDraw as schem', 'import schemdraw')
            
            # Replace various AND gate patterns with logic.And()
            code = re.sub(r'e\.AND2|e\.And2|e\.and2|e\.And\(\)|e\.and\(\)|e\.andgate\(\)|e\.ANDGATE\(\)|e\.andgate\(\)', 'logic.And()', code)
            code = re.sub(r'd\.add\((.*?)\)', r'd += \1', code)
            
            # Fix all .save() patterns to use buffer
            code = re.sub(r'\.save\([\'"][^\'"]*[\'"]\)', '.save(buffer)', code)
            
            # Remove .output() calls which don't exist in schemdraw
            code = re.sub(r'\.output\(\)', '', code)
            code = re.sub(r'\.outputs\([^)]*\)', '', code)
            code = re.sub(r'\.inputs\([^)]*\)', '', code)
            code = re.sub(r'\.inputs\([^)]*\)\.outputs\([^)]*\)', '', code)
            
            # Replace schem.Drawing() with schemdraw.Drawing()
            code = code.replace('schem.Drawing()', 'schemdraw.Drawing()')
            
            # Replace d.draw() with d.save(buffer)
            code = code.replace('d.draw()', 'd.save(buffer)')

            # Remove assignment from 'd += ...' lines
            code = re.sub(r'\w+\s*=\s*d \+=', 'd +=', code)
            
            # Fix common syntax errors
            code = re.sub(r'd \+= e\.LINE.*?$', '# d += e.LINE  # Commented out invalid element', code, flags=re.MULTILINE)
            code = re.sub(r'd \+= e\.AND2.*?$', 'd += logic.And()', code, flags=re.MULTILINE)
            code = re.sub(r'd \+= e\.OR2.*?$', 'd += logic.Or()', code, flags=re.MULTILINE)
            
            # Fix Rectangle -> Rect (schemdraw uses Rect, not Rectangle)
            code = re.sub(r'e\.Rectangle', 'e.Rect', code)
            code = re.sub(r'e\.Rectangle\(', 'e.Rect(', code)
            
            # Fix invalid syntax like "d += e.LINE, d='left', l=d.unit"
            code = re.sub(r'd \+= e\.LINE.*?d=\'left\'.*?l=d\.unit.*?$', '# Invalid syntax commented out', code, flags=re.MULTILINE)
            
            # Fix color specifications for schemdraw elements
            code = re.sub(r'\.color\([\'"]([^\'"]*)[\'"]\)', r'.color("\1")', code)
            code = re.sub(r'\.fillcolor\([\'"]([^\'"]*)[\'"]\)', r'.fillcolor("\1")', code)
            
            # Fix common color issues - ensure colors are applied correctly
            code = re.sub(r'\.color\(([^)]+)\)\.label\(([^)]+)\)', r'.label(\2).color(\1)', code)
            code = re.sub(r'\.fillcolor\(([^)]+)\)\.label\(([^)]+)\)', r'.label(\2).fillcolor(\1)', code)
            
            # Ensure we have proper imports
            if 'import schemdraw' not in code:
                code = 'import schemdraw\nimport schemdraw.logic as logic\nfrom schemdraw import Drawing\n' + code
            
            # Add elements import if code uses 'e.' but doesn't have it
            if re.search(r'\be\.\w+', code) and 'import schemdraw.elements as e' not in code:
                # Insert after the first import line
                lines = code.split('\n')
                for i, line in enumerate(lines):
                    if line.strip().startswith('import '):
                        lines.insert(i + 1, 'import schemdraw.elements as e')
                        break
                code = '\n'.join(lines)
                
            # Ensure we have a Drawing() call
            if 'd = Drawing()' not in code and 'd = schemdraw.Drawing()' not in code:
                code = code.replace('d = schem', 'd = schemdraw.Drawing()')
                if 'd = schemdraw.Drawing()' not in code:
                    code = 'd = schemdraw.Drawing()\n' + code

            # Create buffer for image
            buffer = io.BytesIO()
            
            # Prepare execution environment with restricted globals
            exec_globals = {
                'schemdraw': schemdraw, 
                'elm': elm, 
                'logic': logic,
                'buffer': buffer
            }
            
            print(f"🔍 Executing schemdraw code:\n{code}")
            exec(code, exec_globals)
            
            # Save the buffer to output path
            buffer.seek(0)
            with open(output_path, 'wb') as f:
                f.write(buffer.getvalue())
            
            print(f"✅ Schemdraw diagram saved as: {os.path.basename(output_path)}")
            return os.path.basename(output_path)
            
        except Exception as e:
            error_message = str(e)
            print(f"❌ Schemdraw diagram generation error (attempt {attempt + 1}/{max_retries + 1}): {error_message}")
            
            if attempt < max_retries:
                print(f"🔧 Attempting AI-powered code correction...")
                
                # Try AI-powered error correction
                try:
                    from ..openai_service import ai_correct_diagram_code
                    
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
                        library_name="schemdraw",
                        subject=subject,
                        topic=topic
                    )
                    
                    if correction_success and corrected_code != code:
                        print(f"✅ AI provided corrected schemdraw code, attempting execution...")
                        
                        # Apply schemdraw-specific fixes to corrected code
                        corrected_code = apply_schemdraw_fixes(corrected_code, output_path)
                        
                        # Update code for next iteration
                        code = corrected_code
                        continue
                    else:
                        print(f"❌ AI correction failed or provided same code")
                        
                except Exception as ai_error:
                    print(f"❌ AI correction failed: {ai_error}")
                
                # Fallback: basic error pattern fixes
                print(f"🔄 Trying basic schemdraw error fixes...")
                try:
                    fixed_code = fix_common_syntax_errors(code)
                    if fixed_code != code:
                        code = fixed_code
                        continue
                except:
                    pass
            else:
                print(f"❌ All retry attempts failed for schemdraw diagram generation")
                return None 

def apply_schemdraw_fixes(code, output_path):
    """Apply standard schemdraw code fixes and transformations"""
    import re
    import os
    
    # Fix buffer references - use proper filename only
    filename = os.path.basename(output_path)
    code = code.replace('buffer', f"'{filename}'")
    code = code.replace('d.save(buffer', f'd.save("{filename}"')
    
    # Fix hardcoded PNG filenames in d.save() calls
    code = re.sub(r'd\.save\([\'"][^\'"]*.png[\'"]', f'd.save("{filename}"', code)
    
    # Add missing imports if needed
    if 'import schemdraw' not in code and 'schemdraw.' in code:
        code = 'import schemdraw\n' + code
    if 'import schemdraw.logic as logic' not in code and 'logic.' in code:
        code = 'import schemdraw.logic as logic\n' + code
    if 'import schemdraw.elements as e' not in code and 'e.' in code:
        code = 'import schemdraw.elements as e\n' + code
    
    return code

def fix_common_syntax_errors(code: str) -> str:
    """Fix common syntax errors in schemdraw code"""
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