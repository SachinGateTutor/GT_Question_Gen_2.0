import schemdraw
import schemdraw.elements as elm
import schemdraw.logic as logic
import matplotlib
matplotlib.use('Agg')
import io
import traceback
import re
import os
from ..openai_service import ai_correct_diagram_code

def render(code: str, output_path: str):
    """Render schemdraw diagram with AI-powered self-healing"""
    
    # Apply schemdraw-specific fixes
    code = apply_schemdraw_fixes(code, output_path)
        
    # AI-powered self-healing execution with retry mechanism
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            # Clean up the code first
            code = clean_schemdraw_code(code)

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
                print(f"❌ Diagram generation failed - no misleading fallback will be generated")
                return None 

def apply_schemdraw_fixes(code, output_path):
    """Apply schemdraw-specific fixes to the code"""
    import re
    
    # Replace buffer with actual filename
    filename = os.path.basename(output_path)
    code = code.replace('buffer', f"'{filename}'")
    
    return code

def clean_schemdraw_code(code: str) -> str:
    """Clean and fix schemdraw code for common AI mistakes"""
    import re
    
    # Fix library name variations
    code = code.replace('SchemDraw', 'schemdraw')
    code = code.replace('import schemdraw as schem', 'import schemdraw')
    code = code.replace('import SchemDraw as schem', 'import schemdraw')
    code = code.replace('import SchemDraw', 'import schemdraw')
    code = code.replace('import schemdraw as schem', 'import schemdraw')
    
    # Fix import statements
    code = code.replace('import SchemDraw.elements as e', 'import schemdraw.elements as e')
    code = code.replace('import schemdraw.elements as e', 'import schemdraw.elements as e')
    
    # Fix Drawing() calls
    code = code.replace('schem.Drawing()', 'schemdraw.Drawing()')
    code = code.replace('d = Drawing()', 'd = schemdraw.Drawing()')
    
    # Fix save() calls to use buffer
    code = re.sub(r'd\.save\([\'"][^\'"]*[\'"]\)', 'd.save(buffer)', code)
    code = re.sub(r'd\.save\([^)]*\)', 'd.save(buffer)', code)
    code = code.replace('d.draw()', 'd.save(buffer)')
    
    # Fix element names - case sensitive!
    code = re.sub(r'e\.Box\(\)', 'e.Rect()', code)  # Box doesn't exist, use Rect
    code = re.sub(r'e\.Box', 'e.Rect', code)  # Also catch Box without parentheses
    code = re.sub(r'e\.Rectangle', 'e.Rect', code)
    code = re.sub(r'e\.rectangle', 'e.Rect', code)  # lowercase version
    code = re.sub(r'elements\.rectangle', 'e.Rect', code)  # from imports
    code = re.sub(r'e\.DOT\(\)', 'e.Dot()', code)  # DOT -> Dot (case sensitive)
    code = re.sub(r'e\.DOT', 'e.Dot', code)
    code = re.sub(r'e\.LINE\(\)', 'e.Line()', code)  # LINE -> Line
    code = re.sub(r'e\.LINE', 'e.Line', code)
    code = re.sub(r'e\.ARROWHEAD\(\)', 'e.Arrow()', code)  # ARROWHEAD -> Arrow
    code = re.sub(r'e\.ARROWHEAD', 'e.Arrow', code)
    code = re.sub(r'e\.ARROW\(\)', 'e.Arrow()', code)  # ARROW -> Arrow
    code = re.sub(r'e\.ARROW', 'e.Arrow', code)
    code = re.sub(r'e\.RECT\(\)', 'e.Rect()', code)  # RECT -> Rect
    code = re.sub(r'e\.RECT', 'e.Rect', code)
    code = re.sub(r'e\.Dot_OPEN\(\)', 'e.Dot()', code)  # Dot_OPEN doesn't exist
    code = re.sub(r'e\.Dot_OPEN', 'e.Dot', code)
    code = re.sub(r'e\.AND2|e\.And2|e\.and2', 'logic.And()', code)
    code = re.sub(r'e\.OR2|e\.Or2|e\.or2', 'logic.Or()', code)
    
    # Fix invalid parameters in element calls
    code = re.sub(r'e\.(\w+)\(d=[\'"][^\'"]*[\'"]\)', r'e.\1()', code)  # Remove d='right' etc
    code = re.sub(r'e\.(\w+)\(l=[\'"][^\'"]*[\'"]\)', r'e.\1()', code)  # Remove l='1/2' etc
    code = re.sub(r'e\.(\w+)\(xy=[^)]*\)', r'e.\1()', code)  # Remove xy= parameters
    code = re.sub(r'e\.(\w+)\(botlabel=[^)]*\)', r'e.\1()', code)  # Remove botlabel
    code = re.sub(r'e\.(\w+)\(lftlabel=[^)]*\)', r'e.\1()', code)  # Remove lftlabel
    
    # Fix d.add() to d +=
    code = re.sub(r'd\.add\((.*?)\)', r'd += \1', code)
    # Also fix assignments like "alu = d.add(...)"
    # Just remove the assignment part since schemdraw elements can't be referenced this way
    code = re.sub(r'\w+\s*=\s*d\.add\((.*?)\)', r'd += \1', code)
    
    # Remove invalid method calls
    code = re.sub(r'\.N\b', '', code)  # Remove .N references
    code = re.sub(r'\.E\b', '', code)  # Remove .E references
    code = re.sub(r'\.S\b', '', code)  # Remove .S references
    code = re.sub(r'\.W\b', '', code)  # Remove .W references
    
    # Fix invalid positioning - schemdraw doesn't support .at() with tuples
    # First, handle the specific pattern that causes extra parentheses
    code = re.sub(r'(e\.\w+\(\))\.at\(\([^)]*\)\)', r'\1', code)  # e.DOT().at((1,0)) -> e.DOT()
    code = re.sub(r'(e\.\w+\(\))\.at\([^)]*\)', r'\1', code)  # e.DOT().at(...) -> e.DOT()
    
    # Then remove remaining .at(), .to(), .length() calls
    code = re.sub(r'\.at\(\([^)]*\)\)', '', code)  # Remove .at((x,y))
    code = re.sub(r'\.at\([^)]*\)', '', code)  # Remove other .at() calls
    code = re.sub(r'\.to\([^)]*\)', '', code)  # Remove .to() calls
    code = re.sub(r'\.length\([^)]*\)', '', code)  # Remove .length() calls
    
    # Fix invalid methods that don't exist in schemdraw
    code = re.sub(r'\.anchor\([^)]*\)', '', code)  # Remove .anchor() calls
    code = re.sub(r'\.endstyle\([^)]*\)', '', code)  # Remove .endstyle() calls
    code = re.sub(r'\.right\([^)]*\)', '', code)  # Remove .right() calls
    code = re.sub(r'\.tox\([^)]*\)', '', code)  # Remove .tox() calls
    code = re.sub(r'\.lftlabel\([^)]*\)', '.label', code)  # Fix lftlabel -> label
    code = re.sub(r'\.d\([^)]*\)', '', code)  # Remove .d() calls
    code = re.sub(r'\.l\([^)]*\)', '', code)  # Remove .l() calls
    code = re.sub(r'\.xy\([^)]*\)', '', code)  # Remove .xy() calls
    code = re.sub(r'\.center', '', code)  # Remove .center references
    code = re.sub(r'\.end', '', code)  # Remove .end references
    
    # Fix d.unit references (not available in schemdraw)
    code = re.sub(r'd\.unit', '1', code)  # Replace d.unit with 1
    
    # Fix invalid d.add() syntax
    code = re.sub(r'd\.add\(e\.(\w+),', r'd += e.\1(', code)  # d.add(e.Box, -> d += e.Box(
    code = re.sub(r'd\.add\(e\.(\w+)\(\)', r'd += e.\1()', code)  # d.add(e.Box()) -> d += e.Box()
    
    # Fix specific patterns that cause issues
    # Convert "d += e.Line().at(...).length(...).label(...)" to "d += e.Line().label(...)"
    code = re.sub(r'(e\.Line\(\))(?:\.at\([^)]*\))?(?:\.length\([^)]*\))?', r'\1', code)
    code = re.sub(r'(e\.Arrow\(\))(?:\.at\([^)]*\))?(?:\.to\([^)]*\))?(?:\.length\([^)]*\))?', r'\1', code)
    
    # Fix invalid syntax like "d = schemdraw.Drawing()draw.Drawing(...)"
    code = re.sub(r'd = schemdraw\.Drawing\(\)draw\.Drawing', 'd = schemdraw.Drawing()', code)
    code = re.sub(r'd = schemdraw\.Drawing\(\)[^=]*\.Drawing', 'd = schemdraw.Drawing()', code)
    
    # Fix invalid syntax patterns
    code = re.sub(r'd \+= e\.LINE.*?$', '# Invalid LINE element commented out', code, flags=re.MULTILINE)
    code = re.sub(r'\.at\([^)]*\)\.length\([^)]*\)', '', code)  # Remove invalid .at().length() calls
    
    # Fix specific problematic patterns from logs
    code = re.sub(r'cpu = d \+= e\.Rect\([^)]*\)', 'd += e.Rect()', code)  # Fix variable assignments
    code = re.sub(r'mem = d \+= e\.Rect\([^)]*\)', 'd += e.Rect()', code)  # Fix variable assignments
    code = re.sub(r'control = d \+= e\.Line\([^)]*\)', 'd += e.Line()', code)  # Fix variable assignments
    
    # Fix malformed parentheses and syntax
    code = re.sub(r'\([^)]*l=1/2[^)]*\)', '()', code)  # Remove l=1/2 parameters
    code = re.sub(r'\([^)]*l=1\*2[^)]*\)', '()', code)  # Remove l=1*2 parameters
    code = re.sub(r'\([^)]*d=[\'"][^\'"]*[\'"]\)', '()', code)  # Remove d= parameters
    
    # Fix imports
    # Replace various import patterns with standard imports
    code = re.sub(r'from schemdraw import elements', 'import schemdraw.elements as e', code)
    code = re.sub(r'from schemdraw\.elements import .*', 'import schemdraw.elements as e', code)
    
    # Ensure proper imports
    if 'import schemdraw' not in code:
        code = 'import schemdraw\n' + code
    if 'import schemdraw.elements as e' not in code and ('e.' in code or 'elements.' in code):
        code = 'import schemdraw.elements as e\n' + code
    if 'import schemdraw.logic as logic' not in code and 'logic.' in code:
        code = 'import schemdraw.logic as logic\n' + code
    
    # Ensure Drawing() call exists
    if 'd = schemdraw.Drawing()' not in code:
        code = 'd = schemdraw.Drawing()\n' + code
    
    # Fix common syntax errors
    code = fix_common_syntax_errors(code)
    
    # Final cleanup - ensure parentheses are balanced
    open_parens = code.count('(')
    close_parens = code.count(')')
    if open_parens > close_parens:
        # Add missing closing parentheses at the end of lines that might need them
        lines = code.split('\n')
        for i, line in enumerate(lines):
            line_open = line.count('(')
            line_close = line.count(')')
            if line_open > line_close and not line.strip().endswith(')'):
                lines[i] = line + ')' * (line_open - line_close)
        code = '\n'.join(lines)
    
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
    
    # Clean up any orphaned parentheses from our replacements
    # This handles cases like "e.Dot()).label(...)" -> "e.Dot().label(...)"
    code = re.sub(r'\)\)\.', ').', code)
    
    # Fix unmatched parentheses by adding missing closing parentheses
    open_parens = code.count('(')
    close_parens = code.count(')')
    if open_parens > close_parens:
        code += ')' * (open_parens - close_parens)
    elif close_parens > open_parens:
        # Remove extra closing parentheses
        diff = close_parens - open_parens
        for _ in range(diff):
            if code.endswith(')'):
                code = code[:-1]
    
    return code 

 