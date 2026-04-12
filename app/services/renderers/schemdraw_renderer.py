import schemdraw
import schemdraw.elements as elm
import schemdraw.logic as logic
import matplotlib
matplotlib.use('Agg')
import io
import traceback
import re
import os
import inspect
from ..openai_service import ai_correct_diagram_code

# Comprehensive element mapping for schemdraw compatibility
ELEMENT_MAPPINGS = {
    # Logic gates - map various naming conventions to actual schemdraw elements
    'And': 'elm.Rect',  # Fallback to basic shapes since logic gates may not exist
    'AND': 'elm.Rect', 
    'And2': 'elm.Rect',
    'AND2': 'elm.Rect',
    'AndGate': 'elm.Rect',
    'ANDGATE': 'elm.Rect',
    
    'Or': 'elm.Rect',
    'OR': 'elm.Rect',
    'Or2': 'elm.Rect', 
    'OR2': 'elm.Rect',
    'OrGate': 'elm.Rect',
    'ORGATE': 'elm.Rect',
    
    'Not': 'elm.Rect',
    'NOT': 'elm.Rect',
    'NotGate': 'elm.Rect',
    'NOTGATE': 'elm.Rect',
    'Inverter': 'elm.Rect',
    
    'Nand': 'elm.Rect',
    'NAND': 'elm.Rect',
    'Nand2': 'elm.Rect',
    'NAND2': 'elm.Rect',
    'NandGate': 'elm.Rect',
    
    'Nor': 'elm.Rect',
    'NOR': 'elm.Rect',
    'Nor2': 'elm.Rect',
    'NOR2': 'elm.Rect',
    'NorGate': 'elm.Rect',
    
    'Xor': 'elm.Rect',
    'XOR': 'elm.Rect',
    'Xor2': 'elm.Rect',
    'XOR2': 'elm.Rect',
    'XorGate': 'elm.Rect',
    
    'Xnor': 'elm.Rect',
    'XNOR': 'elm.Rect',
    'Xnor2': 'elm.Rect',
    'XNOR2': 'elm.Rect',
    'XnorGate': 'elm.Rect',
    
    # Input/Output elements
    'Input': 'elm.Rect',
    'INPUT': 'elm.Rect',
    'In': 'elm.Rect',
    'Output': 'elm.Rect', 
    'OUTPUT': 'elm.Rect',
    'Out': 'elm.Rect',
    
    # Basic shapes and elements
    'Box': 'elm.Rect',
    'BOX': 'elm.Rect',
    'Rectangle': 'elm.Rect',
    'RECTANGLE': 'elm.Rect',
    'Rect': 'elm.Rect',
    'RECT': 'elm.Rect',
    
    'Circle': 'elm.Circle',
    'CIRCLE': 'elm.Circle',
    
    'Line': 'elm.Line',
    'LINE': 'elm.Line',
    
    'Dot': 'elm.Dot',
    'DOT': 'elm.Dot',
    'Dot_OPEN': 'elm.Dot',
    
    'Arrow': 'elm.Line',  # Use Line instead of Arrow if Arrow doesn't exist
    'ARROW': 'elm.Line',
    'Arrowhead': 'elm.Line',
    'ARROWHEAD': 'elm.Line',
    
    # Electronic components
    'Resistor': 'elm.Resistor',
    'RESISTOR': 'elm.Resistor',
    'R': 'elm.Resistor',
    
    'Capacitor': 'elm.Capacitor',
    'CAPACITOR': 'elm.Capacitor',
    'C': 'elm.Capacitor',
    
    'Inductor': 'elm.Inductor',
    'INDUCTOR': 'elm.Inductor',
    'L': 'elm.Inductor',
    
    'Ground': 'elm.Ground',
    'GROUND': 'elm.Ground',
    'GND': 'elm.Ground',
    
    'Battery': 'elm.Battery',
    'BATTERY': 'elm.Battery',
    'Voltage': 'elm.Battery',
    
    'Label': 'elm.Label',
    'LABEL': 'elm.Label',
    'Text': 'elm.Label',
    'TEXT': 'elm.Label',
}

# Invalid methods/attributes that should be removed
INVALID_METHODS = [
    'at', 'to', 'length', 'anchor', 'endstyle', 'right', 'left', 'up', 'down',
    'tox', 'toy', 'd', 'l', 'xy', 'center', 'end', 'start', 'N', 'E', 'S', 'W',
    'lftlabel', 'botlabel', 'toplabel', 'rgtlabel'
]

def get_available_elements():
    """Get all actually available elements in current schemdraw installation"""
    available = set()
    
    # Check elm (elements) module
    try:
        for name in dir(elm):
            if not name.startswith('_') and callable(getattr(elm, name)):
                available.add(f'elm.{name}')
    except:
        pass
    
    # Check logic module  
    try:
        for name in dir(logic):
            if not name.startswith('_') and callable(getattr(logic, name)):
                available.add(f'logic.{name}')
    except:
        pass
        
    return available

def validate_element_exists(element_name):
    """Check if an element actually exists in schemdraw"""
    try:
        if element_name.startswith('elm.'):
            return hasattr(elm, element_name[4:]) and callable(getattr(elm, element_name[4:]))
        elif element_name.startswith('logic.'):
            return hasattr(logic, element_name[6:]) and callable(getattr(logic, element_name[6:]))
        return False
    except:
        return False

def render(code: str, output_path: str):
    """Render schemdraw diagram with enhanced AI-powered self-healing"""
    
    # Apply schemdraw-specific fixes
    code = apply_schemdraw_fixes(code, output_path)
        
    # AI-powered self-healing execution with retry mechanism
    max_retries = 3  # Increased retries for better success rate
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            # Clean up the code with progressive enhancement
            code = clean_schemdraw_code(code, attempt)

            # Create buffer for image
            buffer = io.BytesIO()
            
            # Prepare execution environment with restricted globals
            exec_globals = {
                'schemdraw': schemdraw, 
                'elm': elm, 
                'e': elm,  # Common alias
                'elements': elm,  # Another common alias
                'logic': logic,
                'buffer': buffer,
                'io': io,
                'matplotlib': matplotlib
            }
            
            print(f" Executing schemdraw code (attempt {attempt + 1}):\n{code}")
            
            # Validate code before execution
            validation_errors = validate_schemdraw_code(code)
            if validation_errors:
                print(f" Code validation warnings: {', '.join(validation_errors)}")
            
            exec(code, exec_globals)
            
            # Save the buffer to output path
            buffer.seek(0)
            if buffer.getvalue():  # Check if buffer has content
                with open(output_path, 'wb') as f:
                    f.write(buffer.getvalue())
                
                print(f" Schemdraw diagram saved as: {os.path.basename(output_path)}")
                return os.path.basename(output_path)
            else:
                raise Exception("No diagram content generated in buffer")
            
        except Exception as e:
            last_error = e
            error_message = str(e)
            print(f" Schemdraw diagram generation error (attempt {attempt + 1}/{max_retries + 1}): {error_message}")
            
            if attempt < max_retries:
                print(f" Attempting enhanced code correction...")
                
                # Try AI-powered error correction first
                if attempt == 0:
                    try:
                        # Extract context from code comments or use defaults
                        subject = extract_context_from_code(code, "Subject", "Electronics")
                        topic = extract_context_from_code(code, "Topic", "Circuit Diagram")
                        
                        corrected_code, correction_success = ai_correct_diagram_code(
                            original_code=code,
                            error_message=error_message,
                            library_name="schemdraw",
                            subject=subject,
                            topic=topic
                        )
                        
                        if correction_success and corrected_code != code:
                            print(f" AI provided corrected schemdraw code")
                            code = apply_schemdraw_fixes(corrected_code, output_path)
                            continue
                        else:
                            print(f" AI correction failed or provided same code")
                            
                    except Exception as ai_error:
                        print(f" AI correction failed: {ai_error}")
                
                # Progressive fallback fixes
                print(f" Applying progressive schemdraw fixes (level {attempt + 1})...")
                try:
                    if attempt == 1:
                        # More aggressive element fixing
                        code = fix_elements_with_fallbacks(code)
                    elif attempt == 2:
                        # Simplify to basic elements only
                        code = simplify_to_basic_elements(code)
                    
                    # Always apply basic syntax fixes
                    code = fix_common_syntax_errors(code)
                    continue
                    
                except Exception as fix_error:
                    print(f" Fix attempt failed: {fix_error}")
            
    print(f" All retry attempts failed for schemdraw diagram generation")
    print(f" Final error: {last_error}")
    print(f" Diagram generation failed - no misleading fallback will be generated")
    return None 

def extract_context_from_code(code, key, default):
    """Extract context information from code comments"""
    try:
        if f'# {key}:' in code:
            return code.split(f'# {key}:')[1].split('\n')[0].strip()
        return default
    except:
        return default

def validate_schemdraw_code(code):
    """Validate schemdraw code and return list of potential issues"""
    issues = []
    
    # Check for common problematic patterns
    if 'e.And(' in code and not validate_element_exists('logic.And2'):
        issues.append("'And' element may not exist, consider using basic shapes")
    
    if 'e.Input(' in code and not validate_element_exists('logic.Buf'):
        issues.append("'Input' element may not exist")
        
    # Check for invalid method calls
    for method in INVALID_METHODS:
        if f'.{method}(' in code:
            issues.append(f"Invalid method '.{method}()' found")
    
    # Check for proper Drawing instantiation
    if 'd = schemdraw.Drawing()' not in code and 'Drawing()' in code:
        issues.append("Missing proper Drawing instantiation")
        
    # Check for save/buffer usage
    if 'd.save(' not in code and 'buffer' in code:
        issues.append("Missing save() call to buffer")
    
    return issues

def apply_schemdraw_fixes(code, output_path):
    """Apply schemdraw-specific fixes to the code"""
    # Replace buffer references with actual filename for save operations
    filename = os.path.basename(output_path)
    
    # Handle various buffer reference patterns
    code = re.sub(r"d\.save\(\s*buffer\s*,\s*fmt\s*=\s*['\"]png['\"]\s*\)", "d.save(buffer)", code)
    code = re.sub(r"\.save\(\s*buffer\s*,\s*fmt\s*=\s*['\"]png['\"]\s*\)", ".save(buffer)", code)
    
    # Ensure buffer is used correctly without fmt parameter
    if 'buffer' not in code and 'd.save(' in code:
        code = re.sub(r'd\.save\([^)]*\)', 'd.save(buffer)', code)
    
    return code

def clean_schemdraw_code(code: str, attempt: int = 0) -> str:
    """Clean and fix schemdraw code with progressive enhancement based on attempt number"""
    
    # Basic cleaning (always applied)
    code = apply_basic_cleaning(code)
    
    # Progressive enhancement based on attempt
    if attempt >= 1:
        code = apply_aggressive_element_mapping(code)
    
    if attempt >= 2:
        code = apply_extreme_simplification(code)
    
    # Always apply final syntax fixes
    code = fix_common_syntax_errors(code)
    code = ensure_proper_structure(code)
    
    return code

def apply_basic_cleaning(code: str) -> str:
    """Apply basic code cleaning and fixes"""
    
    # Fix library name variations
    code = code.replace('SchemDraw', 'schemdraw')
    code = code.replace('import schemdraw as schem', 'import schemdraw')
    code = code.replace('import SchemDraw', 'import schemdraw')
    
    # Fix import statements
    code = re.sub(r'import \w*[Ss]chem[Dd]raw\.elements as \w+', 'import schemdraw.elements as elm', code)
    code = re.sub(r'from schemdraw import elements', 'import schemdraw.elements as elm', code)
    code = re.sub(r'from schemdraw\.elements import .*', 'import schemdraw.elements as elm', code)
    
    # Standardize element access
    code = re.sub(r'\belements\.', 'elm.', code)
    code = re.sub(r'\be\.', 'elm.', code)
    
    # Fix Drawing instantiation
    code = re.sub(r'schem\.Drawing\(\)', 'schemdraw.Drawing()', code)
    code = re.sub(r'(\w+)\.Drawing\(\)', 'schemdraw.Drawing()', code)
    
    # Fix d.add() to d += syntax but avoid variable assignments
    code = re.sub(r'd\.add\((.*?)\)', r'd += \1', code)
    # Remove variable assignments with d += (they're invalid in schemdraw)
    code = re.sub(r'\w+\s*=\s*d\s*\+=', 'd +=', code)
    
    # Remove invalid method calls
    for method in INVALID_METHODS:
        code = re.sub(rf'\.{method}\([^)]*\)', '', code)
        code = re.sub(rf'\.{method}\b', '', code)
    
    # Fix save calls - remove fmt parameter which isn't supported
    code = re.sub(r'd\.save\([^,)]*,\s*fmt=["\'][^"\']*["\']\)', 'd.save(buffer)', code)
    code = re.sub(r'd\.save\([\'"][^\'"]*[\'"]\)', 'd.save(buffer)', code)
    code = re.sub(r'd\.draw\(\)', 'd.save(buffer)', code)
    
    return code

def apply_aggressive_element_mapping(code: str) -> str:
    """Apply aggressive element name mapping"""
    
    # Apply all element mappings
    for old_name, new_name in ELEMENT_MAPPINGS.items():
        # Handle various patterns
        patterns = [
            f'elm.{old_name}',
            f'e.{old_name}', 
            f'elements.{old_name}',
            f'logic.{old_name}'
        ]
        
        for pattern in patterns:
            if validate_element_exists(new_name):
                code = code.replace(f'{pattern}()', f'{new_name}()')
                code = code.replace(f'{pattern}', f'{new_name}')
    
    return code

def apply_extreme_simplification(code: str) -> str:
    """Apply extreme simplification - use only basic guaranteed elements"""
    
    # Map everything to basic shapes that should always exist
    basic_mappings = {
        # All logic gates become rectangles with labels
        r'logic\.\w+\(\)': 'elm.Rect().label("GATE")',
        r'elm\.And\w*\(\)': 'elm.Rect().label("AND")',
        r'elm\.Or\w*\(\)': 'elm.Rect().label("OR")',
        r'elm\.Not\w*\(\)': 'elm.Rect().label("NOT")',
        r'elm\.Nand\w*\(\)': 'elm.Rect().label("NAND")',
        r'elm\.Nor\w*\(\)': 'elm.Rect().label("NOR")',
        r'elm\.Xor\w*\(\)': 'elm.Rect().label("XOR")',
        
        # Ensure basic elements exist
        r'elm\.Box\(\)': 'elm.Rect()',
        r'elm\.Rectangle\(\)': 'elm.Rect()',
        r'elm\.DOT\(\)': 'elm.Dot()',
        r'elm\.LINE\(\)': 'elm.Line()',
        r'elm\.ARROW\(\)': 'elm.Line()',
    }
    
    for pattern, replacement in basic_mappings.items():
        code = re.sub(pattern, replacement, code)
    
    return code

def fix_elements_with_fallbacks(code: str) -> str:
    """Fix elements with intelligent fallbacks"""
    
    # Check what's actually available and provide smart fallbacks
    available_elements = get_available_elements()
    
    # Logic gate fallbacks
    logic_fallbacks = {
        'logic.And': ['logic.And2', 'elm.Rect'],
        'logic.Or': ['logic.Or2', 'elm.Rect'], 
        'logic.Not': ['logic.Not', 'elm.Triangle'],
        'logic.Input': ['logic.Buf', 'elm.Rect'],
        'logic.Output': ['logic.Buf', 'elm.Rect']
    }
    
    for target, fallbacks in logic_fallbacks.items():
        if target in code:
            for fallback in fallbacks:
                if fallback in available_elements:
                    code = code.replace(target, fallback)
                    break
            else:
                # Ultimate fallback to basic rectangle
                code = code.replace(target, 'elm.Rect')
    
    return code

def simplify_to_basic_elements(code: str) -> str:
    """Simplify code to use only the most basic elements"""
    
    # Replace all complex elements with basic shapes
    simplifications = {
        r'logic\.\w+\(\)': 'elm.Rect()',
        r'elm\.(?:And|Or|Not|Input|Output|Gate)\w*\(\)': 'elm.Rect()',
        r'elm\.(?:Resistor|Capacitor|Inductor)\(\)': 'elm.Line()',
        r'elm\.(?:Battery|Voltage)\(\)': 'elm.Line()',
        r'elm\.Ground\(\)': 'elm.Line()',
        r'elm\.(?:Arrow|ARROW)\(\)': 'elm.Line()',
        # Fix invalid elements that got created
        r'elm\.Resistorect\(\)': 'elm.Rect()',
        r'elm\.Inductorine\(\)': 'elm.Line()',
        r'elm\.(\w*ect|\w*ine)\(\)': 'elm.Rect()',  # Catch malformed element names
    }
    
    for pattern, replacement in simplifications.items():
        code = re.sub(pattern, replacement, code)
    
    # Add basic labels to rectangles for clarity (but avoid multiple labels)
    code = re.sub(r'elm\.Rect\(\)(?!.*\.label)', 'elm.Rect().label("GATE")', code)
    
    return code

def fix_common_syntax_errors(code: str) -> str:
    """Fix common syntax errors in schemdraw code"""
    
    # Fix the most critical issue: invalid variable assignments with d +=
    # Remove any variable assignments like "var = d += ..." which cause syntax errors
    code = re.sub(r'^\s*\w+\s*=\s*(d\s*\+=.*)', r'\1', code, flags=re.MULTILINE)
    
    # Fix missing colons (more precise patterns)
    colon_patterns = [
        (r'^(\s*)(for\s+[^:\n#]+)(?<![:\n])\s*\n', r'\1\2:\n'),
        (r'^(\s*)(if\s+[^:\n#]+)(?<![:\n])\s*\n', r'\1\2:\n'),
        (r'^(\s*)(while\s+[^:\n#]+)(?<![:\n])\s*\n', r'\1\2:\n'),
        (r'^(\s*)(def\s+[^:\n#]+)(?<![:\n])\s*\n', r'\1\2:\n'),
        (r'^(\s*)(class\s+[^:\n#]+)(?<![:\n])\s*\n', r'\1\2:\n'),
    ]
    
    for pattern, replacement in colon_patterns:
        code = re.sub(pattern, replacement, code, flags=re.MULTILINE)
    
    # Fix unbalanced parentheses more carefully
    lines = code.split('\n')
    fixed_lines = []
    
    for line in lines:
        if line.strip():
            open_count = line.count('(')
            close_count = line.count(')')
            
            if open_count > close_count:
                # Only add closing parens if line looks like a function call
                if any(pattern in line for pattern in ['d +=', 'elm.', 'logic.']):
                    line += ')' * (open_count - close_count)
            elif close_count > open_count:
                # Remove extra closing parens from the end
                diff = close_count - open_count
                for _ in range(diff):
                    if line.rstrip().endswith(')'):
                        line = line.rstrip()[:-1] + line[len(line.rstrip()):]
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)

def ensure_proper_structure(code: str) -> str:
    """Ensure code has proper structure with necessary imports and setup"""
    
    lines = []
    
    # Ensure imports (avoid duplicates)
    imports_needed = []
    if 'schemdraw' in code and 'import schemdraw' not in code:
        imports_needed.append('import schemdraw')
    if ('elm.' in code or 'elements.' in code) and 'import schemdraw.elements as elm' not in code:
        imports_needed.append('import schemdraw.elements as elm')
    if 'logic.' in code and 'import schemdraw.logic as logic' not in code:
        imports_needed.append('import schemdraw.logic as logic')
    
    # Add missing imports
    for imp in imports_needed:
        if imp not in code:
            lines.append(imp)
    
    # Add the original code
    lines.append(code)
    
    code = '\n'.join(lines)
    
    # Ensure Drawing instantiation
    if 'd = schemdraw.Drawing()' not in code and ('d +=' in code or 'd.save' in code):
        code = 'd = schemdraw.Drawing()\n' + code
    
    # Ensure save call exists and is correct
    if 'd.save(' not in code and 'd +=' in code:
        code += '\nd.save(buffer)'
    
    # Fix any remaining fmt parameters
    code = re.sub(r'd\.save\([^,)]*,\s*fmt\s*=\s*["\'][^"\']*["\']\)', 'd.save(buffer)', code)
    
    return code