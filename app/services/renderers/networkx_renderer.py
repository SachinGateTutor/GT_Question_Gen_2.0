import matplotlib.pyplot as plt
import networkx as nx
import os
import traceback
import re

def render(code: str, output_path: str):
    """Render networkx diagram with AI-powered self-healing"""
    
    # Apply networkx-specific fixes
    code = apply_networkx_fixes(code, output_path)
    
    # AI-powered self-healing execution with retry mechanism
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            plt.clf()
            namespace = {'nx': nx, 'plt': plt}
            exec(code, namespace)
            plt.savefig(output_path)
            print(f"✅ Networkx diagram saved as: {os.path.basename(output_path)}")
            return os.path.basename(output_path)
            
        except Exception as e:
            error_message = str(e)
            print(f"❌ Networkx diagram generation error (attempt {attempt + 1}/{max_retries + 1}): {error_message}")
            
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
    import re
    import os
    
    # Fix color specifications for networkx
    code = re.sub(r'node_color=[\'"]([^\'"]*)[\'"]', r'node_color="\1"', code)
    code = re.sub(r'edge_color=[\'"]([^\'"]*)[\'"]', r'edge_color="\1"', code)
    code = re.sub(r'color=[\'"]([^\'"]*)[\'"]', r'color="\1"', code)
    
    # Fix common networkx color issues
    code = re.sub(r'nc=[\'"]([^\'"]*)[\'"]', r'node_color="\1"', code)
    code = re.sub(r'ec=[\'"]([^\'"]*)[\'"]', r'edge_color="\1"', code)
    
    # Fix buffer references - use proper filename only, not full path
    filename = os.path.basename(output_path)
    code = code.replace('buffer', f"'{filename}'")
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