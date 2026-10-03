import os
import openai
import traceback
import re
import json
import time
import uuid
import random
from dotenv import load_dotenv

from safe_io import safe_print

# Load environment variables from .env file
load_dotenv()

def get_openai_client():
    # Get API key from environment variables
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")

    if os.getenv("FLASK_DEBUG", "").lower() in ("1", "true", "yes"):
        safe_print(f"Debug: OpenAI API key loaded (length {len(api_key)})")
    return openai.OpenAI(api_key=api_key)

def select_optimal_model(task_type, complexity_factors):
    """
    Hybrid model selection based on task complexity and requirements
    
    Args:
        task_type (str): Type of task ('library_selection', 'question_generation', 'bloom_detection', 'topic_analysis', 'cdq_generation')
        complexity_factors (dict): Factors that determine complexity
    
    Returns:
        str: Selected model name
        str: Reason for selection
    """
    
    # Default to GPT-3.5-turbo for cost efficiency
    selected_model = "gpt-3.5-turbo"
    reason = "Cost-effective default choice"
    
    # Complexity scoring system
    complexity_score = 0
    
    # Factor 1: Task Type Complexity
    task_complexity = {
        'library_selection': 1,      # Simple classification task
        'question_generation': 3,     # Complex creative task
        'bloom_detection': 2,         # Analysis task
        'topic_analysis': 3,          # Complex analysis
        'cdq_generation': 4,          # Very complex multi-step task
        'diagram_generation': 3,      # Creative + technical task
        'retry_syntax': 2,            # Technical correction
        'custom_variations': 3        # Creative variations
    }
    
    complexity_score += task_complexity.get(task_type, 2)
    
    # Factor 2: Subject Complexity
    subject = str(complexity_factors.get('subject', '') or '').lower()
    subject_complexity = {
        'machine learning': 4,
        'artificial intelligence': 4,
        'data science': 3,
        'computer science': 3,
        'software engineering': 3,
        'algorithms': 3,
        'data structures': 2,
        'programming': 2,
        'mathematics': 3,
        'physics': 3,
        'chemistry': 2,
        'biology': 2,
        'business': 1,
        'education': 1
    }
    
    for key, value in subject_complexity.items():
        if key in subject:
            complexity_score += value
            break
    
    # Factor 3: Topic Complexity
    topic = str(complexity_factors.get('topic', '') or '').lower()
    topic_complexity = {
        'neural networks': 4,
        'deep learning': 4,
        'reinforcement learning': 4,
        'natural language processing': 4,
        'computer vision': 4,
        'optimization': 3,
        'model evaluation': 3,
        'feature engineering': 3,
        'clustering': 2,
        'classification': 2,
        'regression': 2,
        'arrays': 1,
        'strings': 1,
        'basic concepts': 1
    }
    
    for key, value in topic_complexity.items():
        if key in topic:
            complexity_score += value
            break
    
    # Factor 4: Question Requirements
    requires_diagram = complexity_factors.get('requires_diagram', False)
    requires_option_diagrams = complexity_factors.get('requires_option_diagrams', False)
    is_programming_question = complexity_factors.get('is_programming_question', False)
    
    if requires_diagram:
        complexity_score += 2
    if requires_option_diagrams:
        complexity_score += 3  # More complex than single diagram
    if is_programming_question:
        complexity_score += 2
    
    # Factor 5: Bloom Level
    bloom_level = complexity_factors.get('bloom_level_id', 3)
    if isinstance(bloom_level, str) and bloom_level.isdigit():
        bloom_level = int(bloom_level)
    elif isinstance(bloom_level, str):
        bloom_level = 3  # Default to Apply level
    
    # Higher Bloom levels (4-6) are more complex
    if bloom_level >= 4:
        complexity_score += 2
    elif bloom_level >= 5:
        complexity_score += 3
    
    # Factor 6: Custom Prompt Complexity
    custom_prompt = str(complexity_factors.get('custom_prompt', '') or '')
    if custom_prompt and len(custom_prompt) > 100:
        complexity_score += 1
    if custom_prompt and any(keyword in custom_prompt.lower() for keyword in ['complex', 'advanced', 'detailed', 'comprehensive']):
        complexity_score += 2
    
    # Factor 7: Number of Questions
    num_questions = complexity_factors.get('num_questions', 1)
    if num_questions > 3:
        complexity_score += 1
    if num_questions > 5:
        complexity_score += 2
    
    # Decision Logic
    # gpt-4o-mini is used for all question_generation tasks regardless of score
    # to ensure factual accuracy. gpt-3.5-turbo is only kept for low-cost
    # auxiliary tasks (library_selection, bloom_detection, retry_syntax).
    if task_type == 'question_generation' or task_type == 'cdq_generation' or task_type == 'topic_analysis':
        selected_model = "gpt-4o-mini"
        reason = f"Factual accuracy required (score: {complexity_score}) - using gpt-4o-mini"
    elif complexity_score >= 8:
        selected_model = "gpt-4o-mini"
        reason = f"High complexity task (score: {complexity_score}) - requires advanced reasoning"
    elif complexity_score >= 6:
        selected_model = "gpt-4o-mini"
        reason = f"Medium-high complexity (score: {complexity_score}) - benefits from advanced model"
    elif complexity_score >= 4:
        selected_model = "gpt-3.5-turbo"
        reason = f"Medium complexity (score: {complexity_score}) - balanced approach"
    else:
        selected_model = "gpt-3.5-turbo"
        reason = f"Low complexity (score: {complexity_score}) - cost-effective choice"
    
    safe_print(f" Model Selection: {selected_model} - {reason}")
    safe_print(f" Complexity Score: {complexity_score} (Task: {task_type}, Subject: {subject}, Topic: {topic})")
    
    return selected_model, reason

def determine_best_library(subject, topic, requires_diagram):
    """Stage 1: Determine the best library for the given subject/topic"""
    if not requires_diagram:
        return None, None
    
    client = get_openai_client()
    
    # Use hybrid model selection
    complexity_factors = {
        'subject': subject,
        'topic': topic,
        'requires_diagram': requires_diagram
    }
    selected_model, model_reason = select_optimal_model('library_selection', complexity_factors)
    
    library_prompt = f"""
For the subject '{subject}' and topic '{topic}', determine the best Python library to generate a relevant diagram.

Available libraries and their strengths:
1. **schemdraw** - Electronic circuits, logic gates, simple block diagrams, flowcharts, system architecture
2. **matplotlib** - Mathematical plots, charts, graphs, 2D visualizations, scientific plots, algorithms visualization
3. **networkx** - Network graphs, social networks, relationship diagrams, data flow, system architecture, graph algorithms
4. **graphviz** - Flowcharts, process diagrams, hierarchical structures, decision trees, system design, database schemas
5. **plotly** - Interactive charts, 3D plots, statistical visualizations, data analysis, business intelligence
6. **seaborn** - Statistical plots, data visualizations, machine learning results, correlation analysis, distribution plots
7. **pillow** - Image manipulation, simple geometric shapes, pixel art, basic diagrams, educational illustrations
8. **turtle** - Simple geometric drawings, educational diagrams, algorithmic visualization, recursive patterns

Subject-specific considerations:
- **Computer Science**: Use networkx for algorithms, graphviz for data structures, matplotlib for complexity analysis
- **Mathematics**: Use matplotlib for mathematical plots, seaborn for statistical analysis, plotly for 3D visualizations
- **Engineering**: Use schemdraw for circuits, graphviz for system design, matplotlib for engineering calculations
- **Business**: Use plotly for business intelligence, seaborn for data analysis, graphviz for process flows
- **Education**: Use turtle for basic concepts, pillow for simple diagrams, matplotlib for educational plots

Respond with ONLY:
Library: <library_name>
Reason: <brief reason why this library is best for this subject/topic>
"""
    
    try:
        response = client.chat.completions.create(
            model=selected_model,
            messages=[{"role": "user", "content": library_prompt}]
        )
        content = response.choices[0].message.content
        
        # Parse the response
        library_name = None
        reason = None
        
        for line in content.split('\n') if content else []:
            if line and line.startswith('Library:'):
                parts = line.split(':', 1)
                if len(parts) > 1:
                    library_name = parts[1].strip()
                    # Strip markdown formatting (**library_name** -> library_name)
                    library_name = library_name.strip('*').strip()
            elif line and line.startswith('Reason:'):
                parts = line.split(':', 1)
                if len(parts) > 1:
                    reason = parts[1].strip()
                    # Strip markdown formatting from reason too
                    reason = reason.strip('*').strip()
        
        safe_print(f" Selected library: {library_name} - {reason}")
        return library_name, reason
        
    except Exception as e:
        safe_print(f"Error determining library: {e}")
        return "schemdraw", "Fallback to schemdraw"

def generate_mcq_and_diagram(data):
    try:
        safe_print(" Debug: Starting generate_mcq_and_diagram")
        safe_print(f" Debug: Input data: {data}")
        
        # Get values from data, with intelligent defaults
        stream = data.get('stream')
        subject = data.get('subject')
        
        # If stream is not provided, try to get it from stream_id via .NET API
        if not stream:
            stream_id = data.get('stream_id')
            if stream_id:
                try:
                    from .net_backend_service import net_backend_service
                    stream_result = net_backend_service.get_stream_by_id(
                        stream_id,
                        auth_token=data.get('auth_token') or data.get('token')
                    )
                    if stream_result.get('success') and stream_result.get('stream_name'):
                        stream = stream_result['stream_name']
                        safe_print(f" Debug: Retrieved stream from .NET backend: {stream} for stream_id: {stream_id}")
                    else:
                        stream = f'Stream {stream_id}'
                except Exception as e:
                    stream = f'Stream {stream_id}'
            else:
                stream = 'CS'  # fallback if no stream_id
        
        # If subject is not provided, try to get it from subject_id
        if not subject:
            subject_id = data.get('subject_id')
            if subject_id:
                try:
                    from .db_service import get_subject_name_by_id
                    subject = get_subject_name_by_id(subject_id)
                    if subject:
                        safe_print(f" Debug: Retrieved subject from DB: {subject} for subject_id: {subject_id}")
                    else:
                        subject = 'Computer Science'  # fallback
                except Exception as e:
                    subject = 'Computer Science'  # fallback
            else:
                subject = 'Computer Science'  # fallback if no subject_id
        
        topic = data.get('topic', 'Programming')
        question_type = data.get('question_type', 'MCQ')
        requires_diagram = data.get('requires_diagram', False)
        requires_option_diagrams = data.get('requires_option_diagrams', False)
        is_programming_question = data.get('is_programming_question', False)
        custom_prompt = data.get('custom_prompt', '')
        
        # Force all values to be string to prevent type errors (e.g. if they are integer IDs due to DB fallback)
        stream = str(stream or 'CS')
        subject = str(subject or 'Computer Science')
        topic = str(topic or 'Programming')
        custom_prompt = str(custom_prompt or '')

        safe_print(f" Debug: Parsed values - stream: {stream}, subject: {subject}, topic: {topic}")
        safe_print(f" Debug: question_type: {question_type}, requires_diagram: {requires_diagram}, requires_option_diagrams: {requires_option_diagrams}")
        
        # Determine the best library for diagram generation
        library_name, library_reason = determine_best_library(subject, topic, requires_diagram)
        
        # Generate the question with retry mechanism for syntax errors
        max_retries = 2
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # Generate the question
                difficulty_level = data.get('difficulty_level')
                if not difficulty_level and data.get('difficulty_level_id') not in (None, ''):
                    from .difficulty_prompts import difficulty_name_from_id
                    difficulty_level = difficulty_name_from_id(data.get('difficulty_level_id'))
                bloom_level = data.get('bloom_level')
                if not bloom_level or bloom_level in ('auto', 'auto_detect'):
                    from .difficulty_prompts import bloom_name_from_id
                    if data.get('bloom_level_id') not in (None, '', 'auto', 'auto_detect'):
                        bloom_level = bloom_name_from_id(data.get('bloom_level_id'))
                    else:
                        bloom_level = None

                topic_summary = data.get('topic_summary')

                if is_programming_question:
                    prompt = generate_programming_question_prompt(
                        topic, question_type, custom_prompt,
                        difficulty_level=difficulty_level, bloom_level=bloom_level,
                        topic_summary=topic_summary
                    )
                elif requires_diagram or requires_option_diagrams:
                    prompt = generate_diagram_question_prompt(
                        topic, subject, stream, question_type, requires_option_diagrams,
                        library_name, custom_prompt,
                        difficulty_level=difficulty_level, bloom_level=bloom_level,
                        topic_summary=topic_summary
                    )
                else:
                    prompt = generate_regular_question_prompt(
                        topic, subject, stream, question_type, custom_prompt,
                        difficulty_level=difficulty_level, bloom_level=bloom_level,
                        topic_summary=topic_summary
                    )
                
                # Use hybrid model selection for question generation
                complexity_factors = {
                    'subject': subject,
                    'topic': topic,
                    'requires_diagram': requires_diagram,
                    'requires_option_diagrams': requires_option_diagrams,
                    'is_programming_question': is_programming_question,
                    'bloom_level_id': data.get('bloom_level_id', 3),
                    'custom_prompt': custom_prompt,
                    'num_questions': data.get('num_questions', 1)
                }
                selected_model, model_reason = select_optimal_model('question_generation', complexity_factors)
                
                # Get OpenAI response
                client = get_openai_client()
                safe_print(" Debug: Sending request to OpenAI...")
                
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.3,
                    max_tokens=2000
                )
                
                safe_print(" Debug: Got response from OpenAI")
                response_text = response.choices[0].message.content
                safe_print("=== RAW OPENAI RESPONSE ===")
                safe_print(response_text)
                safe_print("===========================")

                # Detect model self-correction: model realised its own options are wrong
                # mid-response. Treat this as a bad generation and let the retry loop handle it.
                _self_correction_signals = [
                    "options provided do not include",
                    "correct answer is not",
                    "not in the options",
                    "revise the options",
                    "options should be",
                    "correct the options",
                    "none of the options",
                    "no correct option",
                    "options are incorrect",
                    "answer is not listed",
                    "answer is not among",
                ]
                _response_lower = response_text.lower()
                _self_correction_found = next(
                    (s for s in _self_correction_signals if s in _response_lower), None
                )
                if _self_correction_found:
                    raise ValueError(
                        f"Model self-corrected mid-response (detected: '{_self_correction_found}'). "
                        f"Retrying generation (attempt {retry_count + 1}/{max_retries + 1})."
                    )
                
                # Parse the response
                parsed_result = parse_openai_response(response_text)
                
                # Force correct library detection for option diagrams
                if requires_option_diagrams:
                    option_codes = parsed_result.get('option_diagram_codes', {})
                    
                    # Check if any option contains graphviz code and force library detection
                    for option, code in option_codes.items():
                        if code and ('graphviz' in code or 'dot.node' in code or 'dot.edge' in code):
                            parsed_result['library_used'] = 'graphviz'
                            safe_print(" Debug: Forced library to graphviz based on option code analysis")
                            break
                    
                    # Also check main diagram code
                    if parsed_result.get('diagram_code') and 'graphviz' in parsed_result['diagram_code']:
                        parsed_result['library_used'] = 'graphviz'
                        safe_print(" Debug: Forced library to graphviz based on main diagram code")
                    
                    # Handle missing options with fallback generation
                    import time
                    missing_options = []
                    for option in ['A', 'B', 'C', 'D']:
                        if option not in option_codes or not option_codes[option]:
                            missing_options.append(option)
                    
                    if missing_options:
                        safe_print(f" Debug: Missing options: {missing_options} - generating fallbacks")
                        
                        # Generate fallback code for missing options
                        for option in missing_options:
                            fallback_code = f"""import graphviz
import time
import uuid
dot = graphviz.Digraph()
dot.node('A', 'Option {option}', shape='box', style='filled', fillcolor='lightblue')
dot.node('B', 'Data {option}', shape='ellipse', style='filled', fillcolor='lightgreen')
dot.edge('A', 'B', label='relation')
unique_filename = f"graphviz_fallback_{option}_{{int(time.time())}}"
dot.render(unique_filename, format='png', cleanup=True)"""
                            option_codes[option] = fallback_code.strip()
                            safe_print(f" Debug: Generated fallback code for Option {option}")
                        
                        # Update the parsed result
                        parsed_result['option_diagram_codes'] = option_codes
                
                # Enhanced debugging for option diagrams
                if requires_option_diagrams:
                    safe_print(f" Debug: Option diagrams requested - checking AI response...")
                    option_codes = parsed_result.get('option_diagram_codes', {})
                    safe_print(f" Debug: Found option diagram codes: {list(option_codes.keys())}")
                    
                    # Check if response contains expected sections
                    for option in ['A', 'B', 'C', 'D']:
                        if f"Option{option}Code:" in response_text:
                            safe_print(f" Debug: Found Option{option}Code section in response")
                        else:
                            safe_print(f" Debug: Missing Option{option}Code section in response")
                    
                    if not option_codes or not any(option_codes.values()):
                        safe_print(" Debug: No valid option diagram codes parsed!")
                        safe_print(" Debug: This indicates the AI did not follow option diagram format instructions")
                
                # If we have diagram code, validate syntax before proceeding
                if parsed_result.get('diagram_code') and requires_diagram:
                    try:
                        import ast as ast_module
                        ast_module.parse(parsed_result['diagram_code'])
                        safe_print(" Debug: Diagram code syntax is valid")
                    except SyntaxError as syntax_error:
                        safe_print(f" Debug: Syntax error in diagram code: {syntax_error}")
                        if retry_count < max_retries:
                            retry_count += 1
                            safe_print(f" Debug: Retrying diagram generation (attempt {retry_count}/{max_retries})")
                            
                            # Create a retry prompt with the syntax error
                            retry_prompt = f"""
The previous diagram code had a syntax error: {syntax_error}

Please generate a new diagram code that fixes this syntax error. The code should:
1. Have proper indentation in all loops and conditionals
2. Have properly matched parentheses and brackets
3. Use correct Python syntax
4. Generate a relevant diagram for the topic: {topic}

Generate ONLY the corrected diagram code without any explanation:
"""
                            
                            # Use hybrid model selection for retry
                            retry_complexity_factors = {
                                'subject': subject,
                                'topic': topic,
                                'requires_diagram': requires_diagram
                            }
                            retry_model, retry_reason = select_optimal_model('retry_syntax', retry_complexity_factors)
                            
                            retry_response = client.chat.completions.create(
                                model=retry_model,
                                messages=[{"role": "user", "content": retry_prompt}],
                                temperature=0.3,
                                max_tokens=1000
                            )
                            
                            retry_code = retry_response.choices[0].message.content.strip()
                            
                            # Validate the retry code
                            try:
                                import ast as ast_module
                                ast_module.parse(retry_code)
                                safe_print(" Debug: Retry code syntax is valid")
                                parsed_result['diagram_code'] = retry_code
                            except SyntaxError as retry_error:
                                safe_print(f" Debug: Retry code still has syntax error: {retry_error}")
                                # If retry also fails, set diagram_code to None
                                parsed_result['diagram_code'] = None
                                parsed_result['diagram_image_url'] = None
                        else:
                            safe_print(" Debug: Max retries reached, setting diagram to None")
                            parsed_result['diagram_code'] = None
                            parsed_result['diagram_image_url'] = None
                
                # If we have option diagram codes, validate their syntax
                if parsed_result.get('option_diagram_codes') and requires_option_diagrams:
                    for option, code in parsed_result['option_diagram_codes'].items():
                        if code:
                            try:
                                import ast as ast_module
                                ast_module.parse(code)
                            except SyntaxError as syntax_error:
                                safe_print(f" Debug: Syntax error in option {option} diagram code: {syntax_error}")
                                # Set the problematic option code to None
                                parsed_result['option_diagram_codes'][option] = None
                
                # Remove A-heavy bias: shuffle options and remap correct letter + option diagram keys
                parsed_result = apply_mcq_option_shuffle(parsed_result)
                if parsed_result.get('error'):
                    return parsed_result
                
                # Auto-detect Bloom level if requested
                bloom_level_id = data.get('bloom_level_id')
                if bloom_level_id == 'auto' or bloom_level_id == 'auto_detect':
                    safe_print(f" Debug: Auto-detecting Bloom level for question...")
                    detected_bloom_level = auto_detect_bloom_level(
                        parsed_result.get('question_text', ''),
                        parsed_result.get('explanation', ''),
                        topic,
                        subject
                    )
                    parsed_result['detected_bloom_level_id'] = detected_bloom_level
                    safe_print(f" Debug: Auto-detected Bloom level: {detected_bloom_level}")
                
                return parsed_result
                
            except Exception as e:
                error_str = str(e)
                safe_print(f" Debug: Error in generate_mcq_and_diagram: {e}")
                
                # Handle specific OpenAI API errors
                if "Error code: 429" in error_str or "exceeded your current quota" in error_str:
                    safe_print(" OpenAI API quota exceeded - switching to fallback mode")
                    return {
                        'error': 'OpenAI API quota exceeded',
                        'fallback_mode': True
                    }
                elif "Error code: 401" in error_str:
                    safe_print(" OpenAI API authentication failed")
                    return {
                        'error': 'OpenAI API authentication failed',
                        'auth_error': True
                    }
                
                if retry_count < max_retries:
                    retry_count += 1
                    safe_print(f" Debug: Retrying entire generation (attempt {retry_count}/{max_retries})")
                    # Add exponential backoff for rate limits
                    if "rate" in error_str.lower() or "429" in error_str:
                        import time
                        wait_time = 2 ** retry_count  # 2, 4, 8 seconds
                        safe_print(f" Waiting {wait_time} seconds before retry...")
                        time.sleep(wait_time)
                    continue
                else:
                    safe_print(" Debug: Max retries reached, returning error")
                    return {
                        'error': f'Failed to generate question after {max_retries} retries: {str(e)}'
                    }
        
    except Exception as e:
        safe_print(f" Debug: Critical error in generate_mcq_and_diagram: {e}")
        import traceback
        traceback.print_exc()
        return {
            'error': f'Critical error: {str(e)}'
        }

def wrap_math_latex(text):
    if not text:
        return text
    # Only wrap if not already inside $...$
    # This regex matches math-like expressions not already inside $...$
    def replacer(match):
        expr = match.group(0)
        if expr.startswith('$') and expr.endswith('$'):
            return expr
        return f'${expr}$'
    # Match common math patterns: numbers, variables, operators, exponents, fractions, sqrt, Greek letters
    math_patterns = [
        r'\b\d+\s*[+\-*/^]\s*\d+\b',  # 2 + 2, 3*4, etc.
        r'\b\d+x\b',                     # 2x
        r'\b[a-zA-Z]\^\d+\b',           # x^2
        r'\b\d+\^\d+\b',               # 2^3
        r'\\frac\{[^}]+\}\{[^}]+\}',  # \frac{a}{b}
        r'\\sqrt\{[^}]+\}',             # \sqrt{x}
        r'\\[a-zA-Z]+',                   # \pi, \theta, etc.
        r'\b[a-zA-Z]\b',                  # single variable
    ]
    pattern = re.compile('|'.join(math_patterns))
    # Only wrap if not already inside $...$
    def wrap_if_needed(match):
        expr = match.group(0)
        # Don't double-wrap
        if expr.startswith('$') and expr.endswith('$'):
            return expr
        return f'${expr}$'
    # Only wrap if not already inside $...$
    # But don't wrap inside words
    return pattern.sub(wrap_if_needed, text)

def get_library_specific_prompt(library_name):
    """Get library-specific prompt instructions with enhanced visual diversity and exact structure"""
    prompts = {
        'schemdraw': """import schemdraw
import schemdraw.elements as e
import schemdraw.flow as flow
import schemdraw.logic as logic
from schemdraw import Drawing

# Create a RICH, DIVERSE schemdraw diagram with multiple elements
d = schemdraw.Drawing()
# Add diverse elements with colors, labels, and annotations
# Use different shapes, colors, and connections to create an illustrative diagram
# IMPORTANT: Always apply colors AFTER labels to ensure proper rendering
# Example: d += e.Resistor().label('R1').color('red')
# Example: d += logic.And().label('AND').color('blue')
# Example: d += flow.Start().label('START').color('green')
# Example: d += e.Box().label('Process').fillcolor('lightblue').color('darkblue')
d.save(buffer)""",
        
        'matplotlib': """import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import time
import uuid

# Create RICH, COLORFUL matplotlib visualization
plt.style.use('default')  # Use modern styling
fig, ax = plt.subplots(figsize=(10, 8))

# CRITICAL RULES for matplotlib:
# 1. Use 'color' parameter, NOT 'c', 'fc', 'ec', or 'ecolor'
# 2. Use 'facecolor' for fill colors, NOT 'fcolor', 'facedgecolor', 'facedgedgecolor'
# 3. Use 'edgecolor' for border colors, NOT 'ecolor', 'edgedgecolor', 'edgefacecolor'
# 4. NEVER combine parameter names: NO 'facedgedgecolor', 'faceedgecolor', 'edgefacecolor'
# 5. Valid bbox parameters: facecolor='color', edgecolor='color', boxstyle='style'
# 6. Always use plt.savefig() with proper filename
# 7. Always call plt.close() after saving
# 8. CRITICAL: Ensure all for loops have proper indentation
# 9. CRITICAL: Check all parentheses and brackets are properly matched
# 10. CRITICAL: Use proper Python syntax - no missing colons or indentation

# Add diverse plot elements with colors, markers, and annotations
# Create an informative and visually appealing plot
# Example: ax.plot(x, y, color='red', linewidth=2, marker='o')
# Example: ax.scatter(x, y, color='blue', s=100, alpha=0.6)
# Example: ax.bar(categories, values, color='green', alpha=0.7)
# Example: ax.fill_between(x, y1, y2, color='lightblue', alpha=0.3)

# MANDATORY bbox examples - USE EXACTLY THESE:
# ax.text(x, y, 'label', bbox=dict(facecolor='white', edgecolor='black'))
# ax.annotate('text', xy=(x, y), bbox=dict(facecolor='yellow', edgecolor='red'))
# 
# FORBIDDEN PARAMETERS (WILL CAUSE ERRORS):
#  facedgedgecolor  faceedgecolor  edgefacecolor  edgedgecolor 
#  ecolor  fcolor  edgedgedgecolor  Any combined parameter names
#
# ONLY USE: facecolor='value' and edgecolor='value' - NOTHING ELSE!

# CRITICAL: Always ensure proper indentation in loops and conditionals
# Example of proper for loop:
# for i in range(5):
#     ax.plot(x, y, color='red')  # Proper indentation

# Use time-based filename to avoid conflicts
unique_filename = f"matplotlib_{uuid.uuid4().hex[:8]}_{int(time.time())}"
plt.savefig(unique_filename, format='png', bbox_inches='tight', dpi=300)
plt.close()""",
        
        'networkx': """import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO

# Create RICH, DIVERSE network graph with multiple elements
G = nx.Graph()
# Add diverse nodes and edges with different colors, sizes, and styles
# Create an illustrative network showing clear relationships
# Example: G.add_node(1, color='red', size=1000, label='Start')
# Example: G.add_edge(1, 2, color='blue', width=3)
nx.draw(G, with_labels=True, font_weight='bold', node_color='lightblue', 
        node_size=1000, edge_color='red', width=2)
plt.savefig(buffer, format='png', bbox_inches='tight')
plt.close()""",
        
        'graphviz': """import graphviz
import time
import uuid
from io import BytesIO

# CRITICAL: Generate ONLY Graphviz diagram code, NOT Python class code
# Create RICH, HIERARCHICAL graphviz diagram with diverse elements
dot = graphviz.Digraph()
# Add diverse nodes and edges with different shapes, colors, and styles
# Create an illustrative diagram showing clear flow and relationships
# Example: dot.node('A', 'Start', shape='ellipse', fillcolor='lightgreen', style='filled')
# Example: dot.edge('A', 'B', label='to decision', color='red', style='dashed')
# CRITICAL: Use dot.edge() for individual edges, NOT dot.edges() with style/color parameters
# CRITICAL: dot.edges() only accepts tuples like [('A', 'B'), ('B', 'C')] - no styling
# CRITICAL: DO NOT generate Python class definitions, methods, or print statements
# CRITICAL: Generate ONLY Graphviz dot.node() and dot.edge() calls
# Note: Use unique filename to avoid conflicts
import uuid
import time
unique_filename = f"graphviz_{uuid.uuid4().hex[:8]}_{int(time.time())}"
dot.render(unique_filename, format='png', cleanup=True)
# The backend will handle reading the file and serving the image""",
        
        'plotly': """import plotly.graph_objects as go
import plotly.io as pio
from io import BytesIO

# Create RICH, INTERACTIVE plotly figure with diverse elements
fig = go.Figure()
# Add diverse traces with colors, markers, and annotations
# Create an informative and visually stunning plot
# Example: fig.add_trace(go.Scatter(x=x, y=y, mode='markers', marker=dict(color='red', size=10)))
# Example: fig.add_trace(go.Bar(x=categories, y=values, marker_color='blue'))
pio.write_image(fig, buffer, format='png', width=800, height=600)""",
        
        'seaborn': """import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from io import BytesIO

# Create BEAUTIFUL, INFORMATIVE seaborn visualization
sns.set_style('whitegrid')
fig, ax = plt.subplots(figsize=(10, 8))
# Add diverse plot elements with colors, styles, and annotations
# Create both beautiful and informative plots
# Example: sns.scatterplot(data=df, x='x', y='y', hue='category', palette='viridis')
# Example: sns.barplot(data=df, x='category', y='value', palette='Set2')
plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
plt.close()""",
        
        'pillow': """from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

# Create RICH, COLORFUL pillow diagram with diverse elements
img = Image.new('RGB', (800, 600), color='white')
draw = ImageDraw.Draw(img)
# Add diverse shapes, colors, text, and annotations
# Create an illustrative and educational diagram
# Example: draw.rectangle([50, 50, 200, 150], fill='lightblue', outline='darkblue', width=3)
# Example: draw.ellipse([50, 200, 150, 300], fill='yellow', outline='orange', width=3)
# Example: draw.text((50, 20), "Title", fill='darkblue', font=font)
img.save(buffer, format='PNG')""",
        
        'turtle': """import turtle
from io import BytesIO

# Create ARTISTIC, EDUCATIONAL turtle drawing with diverse elements
t = turtle.Turtle()
screen = turtle.Screen()
# Add diverse shapes, colors, and patterns
# Create both beautiful and educational drawings
# Example: t.color('red'), t.fillcolor('blue'), t.begin_fill()
# Example: t.forward(100), t.right(90), t.end_fill()
screen.getcanvas().postscript(file=buffer)
screen.bye()"""
    }
    
    return prompts.get(library_name, prompts['schemdraw'])

def get_library_rules(library_name):
    """Get library-specific rules with enhanced diversity and visual appeal"""
    rules = {
        'schemdraw': """1. Use diverse schemdraw elements for rich diagrams:
   - Electronic: e.Resistor2(), e.Capacitor2(), e.Inductor2(), e.Diode(), e.SourceV(), e.SourceI()
   - Logic: logic.And(), logic.Or(), logic.Not(), logic.Nand(), logic.Nor(), logic.Xor()
   - Flow: flow.Start(), flow.Process(), flow.Decision(), flow.End(), flow.Arrow()
   - Shapes: e.Dot(), e.Line(), e.Box(), e.Circle(), e.Ellipse(), e.Rect()
2. Use colors and styling: element.color('red'), element.style('dashed'), element.width(2)
3. Add labels and annotations: element.label('text'), element.up().label('above'), element.down().label('below')
4. Create complex layouts with multiple elements and connections
5. Use different shapes for different concepts (rectangles for processes, circles for data, diamonds for decisions)
6. Always end with: d.save(buffer)
7. Make diagrams illustrative and educational, not just basic shapes
8. IMPORTANT: Apply colors AFTER labels to ensure proper rendering: element.label('text').color('red')""",
        
        'matplotlib': """1. Create rich, colorful visualizations:
   - Use plt.style.use('seaborn-v0_8') for better styling
   - Use diverse plot types: plt.plot(), plt.scatter(), plt.bar(), plt.pie(), plt.hist(), plt.boxplot()
   - Add colors: plt.plot(x, y, color='red', linewidth=2, marker='o')
   - Use different markers: 'o', 's', '^', 'D', '*', '+', 'x'
   - Add grid: plt.grid(True, alpha=0.3)
   - Use multiple subplots: fig, (ax1, ax2) = plt.subplots(1, 2)
   - Add legends, titles, and axis labels
   - Use different line styles: '--', '-.', ':', '-'
   - Add annotations: plt.annotate('text', xy=(x, y))
2. CRITICAL SYNTAX RULES:
   - Always ensure proper indentation in for loops and if statements
   - Check all parentheses and brackets are properly matched
   - Use proper Python syntax - no missing colons or indentation
   - Example of proper for loop:
     for i in range(5):
         ax.plot(x, y, color='red')  # Proper indentation
3. Always end with: plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
4. Always close with: plt.close()
5. Make plots informative and visually appealing
6. IMPORTANT: Use proper color names and ensure colors are applied correctly""",
        
        'networkx': """1. Create diverse network visualizations:
   - Use different graph types: nx.Graph(), nx.DiGraph(), nx.MultiGraph()
   - Use various layouts: nx.spring_layout(), nx.circular_layout(), nx.shell_layout(), nx.kamada_kawai_layout()
   - Add node colors: nx.draw(G, node_color=['red', 'blue', 'green'], node_size=[100, 200, 300])
   - Use different node shapes: nx.draw(G, node_shape='s') # 'o', 's', '^', 'v', '<', '>', 'd', 'p'
   - Add edge colors and styles: nx.draw(G, edge_color='red', width=2, style='dashed')
   - Use different node sizes based on importance
   - Add edge labels: nx.draw_networkx_edge_labels(G, pos)
   - Use different arrow styles for directed graphs
2. Always end with: nx.draw(G, with_labels=True, font_weight='bold') and plt.savefig(buffer)
3. Always close with: plt.close()
4. Make networks show clear relationships and hierarchy
5. IMPORTANT: Use proper color names and ensure colors are applied correctly""",
        
        'graphviz': """1. Create rich, hierarchical diagrams:
   - Use different node shapes: 'box', 'circle', 'ellipse', 'diamond', 'triangle', 'hexagon', 'octagon'
   - Add colors: node [color='red', fillcolor='lightblue', style='filled']
   - Use different edge styles: 'solid', 'dashed', 'dotted', 'bold'
   - Add edge colors: edge [color='red', penwidth=2]
   - Use different arrowheads: 'normal', 'vee', 'box', 'diamond', 'dot'
   - Add node labels with rich text: 'Node\\nSubtitle'
   - Use different graph directions: 'TB', 'LR', 'BT', 'RL'
   - Add subgraphs for grouping: subgraph cluster_0 { ... }
   - Use different font sizes and styles
   - Add tooltips and URLs for interactive elements
2. CRITICAL: For edges, use dot.edge('A', 'B', style='dashed', color='red') NOT dot.edges()
3. CRITICAL: dot.edges() only accepts a list of tuples like [('A', 'B'), ('B', 'C')] - no style/color parameters
4. Use unique filenames: unique_filename = f"graphviz_{uuid.uuid4().hex[:8]}_{int(time.time())}"; dot.render(unique_filename, format='png', cleanup=True)
5. Make diagrams show clear flow and relationships
6. Use appropriate shapes for different concepts (rectangles for processes, diamonds for decisions)
7. IMPORTANT: Use proper color names and ensure colors are applied correctly""",
        
        'plotly': """1. Create interactive, rich visualizations:
   - Use diverse trace types: go.Scatter(), go.Bar(), go.Pie(), go.Histogram(), go.Box(), go.Heatmap()
   - Add colors and styling: marker=dict(color='red', size=10, symbol='diamond')
   - Use different symbols: 'circle', 'square', 'diamond', 'triangle-up', 'star', 'cross'
   - Add hover information: hovertemplate='<b>%{x}</b><br>%{y}<extra></extra>'
   - Use different line styles: line=dict(dash='dash', width=3)
   - Add multiple traces for comparison
   - Use different color scales: colorscale='Viridis', 'Plasma', 'Reds', 'Blues'
   - Add annotations and shapes
   - Use 3D plots when appropriate: go.Scatter3d()
2. Always end with: pio.write_image(fig, buffer, format='png', width=800, height=600)
3. Make plots informative and visually stunning
4. IMPORTANT: Use proper color names and ensure colors are applied correctly""",
        
        'seaborn': """1. Create beautiful statistical visualizations:
   - Use diverse plot types: sns.scatterplot(), sns.lineplot(), sns.barplot(), sns.boxplot(), sns.violinplot(), sns.heatmap()
   - Add colors and styling: palette='husl', 'Set2', 'Paired', 'viridis'
   - Use different markers and line styles
   - Add confidence intervals: ci=95
   - Use different plot sizes: height=6, aspect=1.5
   - Add titles and labels with proper styling
   - Use different themes: sns.set_style('whitegrid'), 'darkgrid', 'white', 'dark'
   - Add regression lines: sns.regplot()
   - Use different color palettes for categorical data
2. Always end with: plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
3. Always close with: plt.close()
4. Make plots both beautiful and informative""",
        
        'pillow': """1. Create rich, colorful diagrams:
   - Use different colors: 'red', 'blue', 'green', 'yellow', 'purple', 'orange', 'pink'
   - Draw diverse shapes: rectangles, circles, ellipses, polygons, lines, arcs
   - Use different line styles: 'solid', 'dashed', 'dotted'
   - Add text with different fonts and sizes
   - Use gradients and patterns
   - Add transparency: fill=(255, 0, 0, 128)
   - Draw arrows and connectors
   - Use different brush sizes and styles
   - Add shadows and 3D effects
   - Create flowcharts and diagrams with multiple elements
2. Always end with: img.save(buffer, format='PNG')
3. Make images illustrative and educational
4. IMPORTANT: Use proper color names and ensure colors are applied correctly""",
        
        'turtle': """1. Create artistic and educational drawings:
   - Use different colors: turtle.color('red'), turtle.fillcolor('blue')
   - Draw diverse shapes: circles, squares, triangles, stars, spirals, fractals
   - Use different pen sizes: turtle.pensize(3)
   - Add patterns and designs
   - Use different speeds: turtle.speed(0) for fastest
   - Create complex geometric patterns
   - Add text and labels
   - Use different line styles and patterns
   - Create educational diagrams with multiple elements
2. Always end with: screen.getcanvas().postscript(file=buffer)
3. Always close with: screen.bye()
4. Make drawings both beautiful and educational
5. IMPORTANT: Use proper color names and ensure colors are applied correctly"""
    }
    
    return rules.get(library_name, rules['schemdraw'])

def _prompt_level_block(difficulty_level=None, bloom_level=None):
    """Difficulty + Bloom instructions for a single generated question."""
    parts = []
    if difficulty_level:
        from .difficulty_prompts import format_difficulty_prompt_block
        parts.append(format_difficulty_prompt_block(difficulty_level))
    if bloom_level:
        parts.append(get_bloom_level_guidance(bloom_level).strip())
        parts.append(f"The question MUST target Bloom level {bloom_level}.")
    if not parts:
        return ""
    return "\n\n" + "\n\n".join(parts) + "\n"


def _topic_scope_block(topic_summary=None):
    """Optional topicSummary scope constraint for question generation prompts."""
    if not topic_summary:
        return ""
    summary = str(topic_summary).strip()
    if not summary:
        return ""
    return (
        f"\nTOPIC SCOPE (use this as the source of truth for what this topic covers):\n"
        f"{summary}\n\n"
        f"Stay inside this scope. Do not introduce concepts that the summary does not cover.\n"
    )


def generate_programming_question_prompt(topic, question_type, custom_prompt, difficulty_level=None, bloom_level=None, topic_summary=None):
    """Generate a prompt for programming questions with code snippets"""
    
    import random
    import time
    
    # Create a seed based on current time to ensure different questions
    random.seed(time.time())
    timestamp_variation = int(time.time() * 1000) % 1000
    
    # Enhanced programming question types for maximum diversity
    programming_question_types = [
        # Code Analysis
        "What will be the output of the following code?",
        "Identify the error in the given code snippet",
        "What will happen when this code is executed?",
        "Which of the following is the correct output?",
        "What is the purpose of the following code?",
        "Which statement about the code is correct?",
        
        # Algorithm Analysis
        "What is the time complexity of the following algorithm?",
        "What is the space complexity of this function?",
        "Which algorithm is being implemented here?",
        "What is the best-case scenario for this algorithm?",
        "What is the worst-case scenario for this algorithm?",
        
        # Data Structure Identification
        "Identify the data structure used in the code",
        "What type of data structure is being implemented?",
        "Which data structure would be most efficient here?",
        "What are the properties of the data structure shown?",
        
        # Problem Solving
        "How would you optimize this code?",
        "What is the most efficient approach to solve this problem?",
        "Which design pattern is being used here?",
        "What would be the next step in this algorithm?",
        
        # Debugging and Testing
        "What is the bug in this code?",
        "Which test case would fail for this function?",
        "What is the root cause of this error?",
        "How would you debug this issue?",
        
        # Code Quality
        "What is the main issue with this code design?",
        "Which principle is being violated here?",
        "How would you refactor this code?",
        "What is the maintainability concern in this code?",
        
        # Performance Analysis
        "Which operation is the bottleneck in this code?",
        "What is the performance impact of this change?",
        "Which optimization would be most effective?",
        "What is the memory usage pattern of this algorithm?",
        
        # Real-world Applications
        "In which scenario would this code be most useful?",
        "What real-world problem does this solve?",
        "Which industry application would benefit from this approach?",
        "What practical limitation does this code have?"
    ]
    
    selected_question_type = random.choice(programming_question_types)
    
    # Enhanced programming languages and topics for maximum diversity
    if 'java' in topic.lower():
        language = 'Java'
        code_example = '''
public class Main {
    public static void main(String[] args) {
        int x = 5;
        System.out.println(x++);
        System.out.println(x);
    }
}'''
    elif 'c++' in topic.lower():
        language = 'C++'
        code_example = '''
#include <iostream>
using namespace std;
int main() {
    int i;
    for (i = 0; i < 5; i++);
    {
        cout << i;
    }
    return 0;
}'''
    elif 'python' in topic.lower():
        language = 'Python'
        code_example = '''
def func(x):
    if x <= 1:
        return 1
    return x * func(x-1)

print(func(5))'''
    elif 'javascript' in topic.lower() or 'js' in topic.lower():
        language = 'JavaScript'
        code_example = '''
function factorial(n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);
}
console.log(factorial(5));'''
    elif 'c#' in topic.lower():
        language = 'C#'
        code_example = '''
using System;
class Program {
    static void Main() {
        int x = 5;
        Console.WriteLine(x++);
        Console.WriteLine(x);
    }
}'''
    elif 'sql' in topic.lower() or 'database' in topic.lower():
        language = 'SQL'
        code_example = '''
SELECT employee_id, salary,
       RANK() OVER (ORDER BY salary DESC) as rank
FROM employees
WHERE department = 'IT';'''
    elif 'algorithm' in topic.lower() or 'data structure' in topic.lower():
        language = 'Pseudocode'
        code_example = '''
function binarySearch(arr, target):
    left = 0
    right = arr.length - 1
    while left <= right:
        mid = (left + right) / 2
        if arr[mid] == target:
            return mid
        else if arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1'''
    elif 'design pattern' in topic.lower():
        language = 'Java'
        code_example = '''
public class Singleton {
    private static Singleton instance;
    private Singleton() {}
    
    public static Singleton getInstance() {
        if (instance == null) {
            instance = new Singleton();
        }
        return instance;
    }
}'''
    elif 'web' in topic.lower() or 'html' in topic.lower():
        language = 'HTML/CSS'
        code_example = '''
<!DOCTYPE html>
<html>
<head>
    <style>
        .container { display: flex; }
        .item { flex: 1; }
    </style>
</head>
<body>
    <div class="container">
        <div class="item">Item 1</div>
        <div class="item">Item 2</div>
    </div>
</body>
</html>'''
    else:
        language = 'Programming'
        code_example = '''
int main() {
    int arr[] = {1, 2, 3, 4, 5};
    int sum = 0;
    for(int i = 0; i < 5; i++) {
        sum += arr[i];
    }
    cout << sum;
    return 0;
}'''
    
    prompt = f"""
Generate a {question_type} question for the topic '{topic}' focusing on programming concepts.
{_topic_scope_block(topic_summary)}
The question MUST include a code snippet in {language} and ask about its output, behavior, or analysis.{_prompt_level_block(difficulty_level, bloom_level)}

IMPORTANT REQUIREMENTS FOR PROGRAMMING QUESTIONS:
1. Use this specific question format: "{selected_question_type}"
2. Include a realistic code snippet that demonstrates the concept
3. Make sure the code has a clear, predictable output or behavior
4. Include common programming concepts like loops, conditionals, functions, data structures
5. Ensure the question tests understanding, not just memorization
6. Use variation {timestamp_variation} to ensure uniqueness

Format your response exactly as follows:

Question: <question text>
Code:
```{language.lower()}
<realistic code snippet>
```
A. <option A with specific output or explanation>
B. <option B with specific output or explanation>
C. <option C with specific output or explanation>
D. <option D with specific output or explanation>
Answer: <correct option letter>
Explanation: <detailed step-by-step explanation of how the code works, line by line, showing the reasoning and output calculation>

CRITICAL RULES:
1. The code must be syntactically correct and executable
2. The output must be predictable and calculable
3. Options should include realistic distractors
4. Explanation should be educational and clear
5. Generate EXACTLY 4 options (A, B, C, D) - no more, no less
"""
    
    if custom_prompt:
        prompt += f"\nSpecial instructions: {custom_prompt}"
    
    return prompt

def get_topic_specific_diagram_guidance(topic: str, subject: str) -> str:
    """Return topic-aware diagram requirements so diagrams are educationally meaningful."""
    t = topic.lower()
    s = subject.lower()

    # Computer Networks / Subnetting / IP Addressing
    if any(k in t or k in s for k in ['subnet', 'network', 'ip address', 'routing', 'topology', 'protocol', 'lan', 'wan', 'tcp', 'udp', 'osi', 'dns', 'dhcp']):
        return """TOPIC-SPECIFIC DIAGRAM RULES (Computer Networks):
- Every subnet/host node MUST show its IP address or CIDR range (e.g., "192.168.1.0/24")
- Include at least one Router or Gateway node clearly labelled as "Router" or with its IP
- Edge labels must describe the link property: bandwidth (e.g., "100 Mbps"), link type ("Ethernet", "WAN", "Fiber"), or protocol
- Do NOT label edges with style names like 'dashed' or 'solid' — those are visual hints only
- Use shapes purposefully: diamond for router/gateway, box for subnet/host, ellipse for cloud/internet
- If showing routing tables or paths, annotate the edges with next-hop IPs or metric costs"""

    # Sorting / Searching Algorithms
    if any(k in t for k in ['sort', 'search', 'binary search', 'bubble', 'merge', 'quick', 'heap sort', 'insertion', 'selection']):
        return """TOPIC-SPECIFIC DIAGRAM RULES (Sorting / Searching Algorithms):
- Nodes must contain ACTUAL numeric values or array elements, not placeholders like "Node A"
- Show the algorithm state at a specific step (e.g., array before/after a swap, pivot element highlighted)
- Edges must indicate the operation happening (e.g., "swap", "compare", "recurse left")
- Highlight the element being processed with a distinct colour (e.g., fillcolor='yellow')
- Include step annotations (e.g., "Step 3: Pivot = 5, Left partition: [2,3], Right: [7,9]")"""

    # Trees (BST, AVL, Heap, Trie, etc.)
    if any(k in t for k in ['tree', 'bst', 'avl', 'heap', 'trie', 'b-tree', 'binary tree', 'red-black']):
        return """TOPIC-SPECIFIC DIAGRAM RULES (Tree Data Structures):
- Nodes must contain ACTUAL key values (e.g., 15, 30, 45) — not "Node A" or "Root"
- Show the complete structural property: BST ordering, heap property (parent ≤ or ≥ children), AVL balance factors
- Label edges with the relationship: "left child", "right child", or the path value
- Use different fill colours for different levels or node types (root, internal, leaf)
- Include a small legend or title explaining what property the diagram demonstrates"""

    # Graph Algorithms (Dijkstra, BFS, DFS, MST)
    if any(k in t for k in ['graph', 'dijkstra', 'bellman', 'floyd', 'bfs', 'dfs', 'traversal', 'mst', 'kruskal', 'prim', 'topological']):
        return """TOPIC-SPECIFIC DIAGRAM RULES (Graph Algorithms):
- Nodes must be labelled with vertex names/IDs (A, B, C or 1, 2, 3)
- Edges MUST show weights or costs as their label (e.g., "4", "12", "0.5") where relevant
- Highlight the path or visited nodes being discussed with distinct colours
- For traversal questions, show the discovery order (e.g., "visited: 1" inside the node)
- For MST questions, distinguish tree edges (bold/coloured) from non-tree edges (grey/dashed)"""

    # Digital Logic / Circuits
    if any(k in t or k in s for k in ['logic', 'gate', 'circuit', 'boolean', 'flip-flop', 'register', 'mux', 'encoder', 'decoder', 'adder', 'electrical', 'electronics']):
        return """TOPIC-SPECIFIC DIAGRAM RULES (Digital Logic / Circuits):
- Show the actual gate type or component clearly labelled (AND, OR, NOT, XOR, MUX, etc.)
- Input/output lines must carry their signal values (0 or 1) or variable names (A, B, Y)
- For truth-table-related questions, include the input combination being evaluated
- Edges (wires) should be labelled with signal names or values, not with style names
- Use shapes that correspond to the component: hexagon for gates, box for registers"""

    # Stacks, Queues, Linked Lists
    if any(k in t for k in ['stack', 'queue', 'linked list', 'deque', 'circular']):
        return """TOPIC-SPECIFIC DIAGRAM RULES (Linear Data Structures):
- Nodes must show ACTUAL data values (e.g., 10, 20, 30) — not generic "Element A"
- Show structural pointers explicitly: TOP/FRONT/REAR markers with arrows
- For linked lists, show the 'next' pointer as an edge labelled "next"
- Indicate NULL / None termination at the end of the list
- For queue operations, show enqueue/dequeue positions with labels"""

    # Operating Systems
    if any(k in t or k in s for k in ['process', 'thread', 'scheduling', 'deadlock', 'memory', 'page', 'os', 'operating system', 'semaphore', 'mutex', 'ipc']):
        return """TOPIC-SPECIFIC DIAGRAM RULES (Operating Systems):
- State diagrams must label each state clearly (Ready, Running, Waiting, Terminated)
- Transition edges must carry the event name (e.g., "I/O request", "scheduler picks", "I/O done")
- For memory diagrams, show actual address ranges and segment names (Code, Stack, Heap)
- For deadlock scenarios, label resource nodes with their resource name and process nodes with PID
- Do NOT use generic edge labels like 'dashed' — always describe what the transition means"""

    # Database / SQL / Relational
    if any(k in t or k in s for k in ['database', 'sql', 'relational', 'er diagram', 'normalization', 'index', 'query', 'table', 'join']):
        return """TOPIC-SPECIFIC DIAGRAM RULES (Databases):
- ER diagram entities must be labelled with their table/entity name and key attributes
- Relationship edges must carry the cardinality notation (1:1, 1:N, M:N) as the label
- For query execution plans, label each node with the operation (Seq Scan, Hash Join, Sort)
- For index structures (B-Tree), show actual key values in nodes
- Do NOT use style names as labels — always use relationship names or cardinality"""

    # Default guidance for all other topics
    return """TOPIC-SPECIFIC DIAGRAM RULES (General):
- Every node label must be meaningful and directly related to the question topic — no placeholders like "Node A" or "Element 1"
- Every edge label must describe the RELATIONSHIP or MEANING of the connection (e.g., "calls", "inherits", "produces", "100ms latency")
- Do NOT use the edge style name ('solid', 'dashed', 'dotted') as the edge label — those are visual decorators only
- Include a title or annotation in the diagram that anchors it to the specific concept being tested
- Use colour purposefully: highlight the key element the question asks about"""


def generate_diagram_question_prompt(topic, subject, stream, question_type, requires_option_diagrams, library_name, custom_prompt, difficulty_level=None, bloom_level=None, topic_summary=None):
    """Generate a prompt for diagram-based questions with enhanced visual diversity"""
    
    import random
    import time
    
    # Create a seed based on current time to ensure different questions
    random.seed(time.time())
    timestamp_variation = int(time.time() * 1000) % 1000
    
    option_diagram_instructions = ""
    if requires_option_diagrams:
        option_diagram_instructions = f"""

 CRITICAL REQUIREMENT: OPTION DIAGRAMS MANDATORY 

You MUST generate 4 separate RICH, DIVERSE diagrams for options A, B, C, and D.
Each option should have its own unique, illustrative diagram that clearly represents the concept described in that option.

FORMAT REQUIREMENT: Your response MUST include ALL of these exact sections (NO EXCEPTIONS):

OptionACode:
```python
[Complete working code for option A diagram]
```

OptionBCode:
```python
[Complete working code for option B diagram]
```

OptionCCode:
```python
[Complete working code for option C diagram]
```

OptionDCode:
```python
[Complete working code for option D diagram]
```

VALIDATION CHECKLIST - Before responding, verify:
 OptionACode section exists with working code
 OptionBCode section exists with working code  
 OptionCCode section exists with working code
 OptionDCode section exists with working code
 All 4 sections have unique, different diagrams

DO NOT include a main PythonCode section - ONLY the four OptionCode sections above.

LIBRARY SPECIFICATION: You must specify "Library: {library_name}" in your response.
DO NOT use "Library: None" - always specify the actual library being used.

VISUAL DIVERSITY REQUIREMENTS:
- Use different colors, shapes, and layouts for each option
- Include multiple elements, connections, and annotations
- Make diagrams educational and visually appealing
- Use appropriate shapes for different concepts (rectangles for processes, diamonds for decisions, circles for data)
- Add labels, titles, and explanatory text
- Use different visual styles and complexity levels

For each option, provide a separate PythonCode block with ACTUAL diagram code:

OptionACode:
```python
# Generate RICH, DIVERSE diagram for Option A with multiple elements, colors, and annotations
import graphviz
import time
import uuid
from io import BytesIO
# Create RICH, HIERARCHICAL graphviz diagram for Option A
dot = graphviz.Digraph()
dot.node('A', 'Root', shape='circle', style='filled', fillcolor="lightblue")
dot.node('B', 'Left Child', shape='box', style='filled', fillcolor="lightgreen")
dot.node('C', 'Right Child', shape='box', style='filled', fillcolor="lightgreen")
dot.edge('A', 'B', label='Root->Left', color="blue", style='dashed')
dot.edge('A', 'C', label='Root->Right', color="blue", style='dashed')
unique_filename = f"graphviz_{uuid.uuid4().hex[:8]}_{int(time.time())}"
dot.render(unique_filename, format='png', cleanup=True)
```

OptionBCode:
```python
# Generate RICH, DIVERSE diagram for Option B with different colors, shapes, and layout
import graphviz
import time
import uuid
from io import BytesIO
# Create RICH, HIERARCHICAL graphviz diagram for Option B
dot = graphviz.Digraph()
dot.node('A', 'Start', shape='ellipse', style='filled', fillcolor="lightgreen")
dot.node('B', 'Process', shape='box', style='filled', fillcolor="lightyellow")
dot.node('C', 'Decision', shape='diamond', style='filled', fillcolor="lightcoral")
dot.edge('A', 'B', label='to process', color="red", style='dashed')
dot.edge('B', 'C', label='to decision', color="blue", style='solid')
unique_filename = f"graphviz_{uuid.uuid4().hex[:8]}_{int(time.time())}"
dot.render(unique_filename, format='png', cleanup=True)
```

OptionCCode:
```python
# Generate RICH, DIVERSE diagram for Option C with unique visual style and elements
import graphviz
import time
import uuid
from io import BytesIO
# Create RICH, HIERARCHICAL graphviz diagram for Option C
dot = graphviz.Digraph()
dot.node('A', 'Input', shape='parallelogram', style='filled', fillcolor="lightcyan")
dot.node('B', 'Process', shape='box', style='filled', fillcolor="lightpink")
dot.node('C', 'Output', shape='ellipse', style='filled', fillcolor="lightyellow")
dot.edge('A', 'B', label='process', color="green", style='bold')
dot.edge('B', 'C', label='result', color="purple", style='dotted')
unique_filename = f"graphviz_{uuid.uuid4().hex[:8]}_{int(time.time())}"
dot.render(unique_filename, format='png', cleanup=True)
```

OptionDCode:
```python
# Generate RICH, DIVERSE diagram for Option D with distinct colors, shapes, and annotations
import graphviz
import time
import uuid
from io import BytesIO
# Create RICH, HIERARCHICAL graphviz diagram for Option D
dot = graphviz.Digraph()
dot.node('A', 'Data', shape='hexagon', style='filled', fillcolor="lightgray")
dot.node('B', 'Analysis', shape='box', style='filled', fillcolor="lightblue")
dot.node('C', 'Result', shape='circle', style='filled', fillcolor="lightgreen")
dot.edge('A', 'B', label='analyze', color="orange", style='dashed')
dot.edge('B', 'C', label='output', color="brown", style='solid')
unique_filename = f"graphviz_{uuid.uuid4().hex[:8]}_{int(time.time())}"
dot.render(unique_filename, format='png', cleanup=True)
```

CRITICAL: Each option diagram should be visually distinct, rich in detail, and clearly represent the concept described in that option.

IMPORTANT: Generate ACTUAL WORKING Python code for each option diagram. Do NOT use placeholder text like "{get_library_specific_prompt(library_name)}" - replace it with real, executable diagram code.

Each OptionACode, OptionBCode, OptionCCode, and OptionDCode must contain complete, working Python code that creates a unique diagram.

 FINAL VALIDATION CHECKLIST - MANDATORY COMPLIANCE 
 OptionACode section exists with UNIQUE working code
 OptionBCode section exists with UNIQUE working code  
 OptionCCode section exists with UNIQUE working code
 OptionDCode section exists with UNIQUE working code
 All 4 sections have DIFFERENT diagrams (NO duplicates)
 All sections use EXACT format "OptionXCode:" (NOT "A.", "B.", etc.)
 NO PythonCode: section exists
 Library specification is provided (NOT "Library: None")

 CRITICAL WARNING: If you use alternative format like "A.", "B.", "C.", "D." instead of "OptionACode:", "OptionBCode:", etc., the system may not parse your response correctly. ALWAYS use the exact "OptionXCode:" format.

FAILURE TO INCLUDE ALL 4 SECTIONS WITH UNIQUE DIAGRAMS WILL RESULT IN GENERIC FALLBACK DIAGRAMS.
YOUR RESPONSE MUST HAVE EXACTLY 4 OPTION CODE SECTIONS - NO EXCEPTIONS!
"""

    # Enhanced question types for maximum diversity
    question_types = [
        # Data Structure Identification
        "Identify the data structure shown in the diagram",
        "Which of the following represents a [specific data structure]?",
        "What type of structure is illustrated below?",
        "Analyze the diagram and determine the data structure",
        "Based on the visual representation, what structure is this?",
        "Examine the diagram and identify the correct data structure",
        "What data structure is being demonstrated here?",
        "Which structure matches the given diagram?",
        
        # Algorithm Analysis
        "What algorithm is being demonstrated in this diagram?",
        "Which sorting algorithm is illustrated below?",
        "What search algorithm is shown in the diagram?",
        "Identify the traversal method being used",
        "What type of algorithm is represented here?",
        
        # Performance Analysis
        "What is the time complexity of the operation shown?",
        "Which operation has the best performance in this scenario?",
        "What is the space complexity of this data structure?",
        "Which approach is most efficient for this problem?",
        
        # Problem Solving
        "How would you solve this problem using the shown approach?",
        "What is the next step in this algorithm?",
        "Which operation would be performed next?",
        "What is the result of applying this operation?",
        
        # Conceptual Understanding
        "What principle is being demonstrated here?",
        "Which concept is illustrated in this diagram?",
        "What property is shown in this structure?",
        "Which characteristic is being highlighted?",
        
        # Application Scenarios
        "In which scenario would this structure be most useful?",
        "What real-world application does this represent?",
        "Which use case is best suited for this approach?",
        "What problem does this solution address?",
        
        # Comparative Analysis
        "Which structure is more efficient for this purpose?",
        "What are the advantages of this approach over others?",
        "Which method would be preferred in this situation?",
        "How does this compare to alternative solutions?"
    ]
    
    # Enhanced data structures and concepts for maximum diversity
    data_structures = [
        # Basic Data Structures
        "Stack", "Queue", "Linked List", "Array", "Hash Table", "Tree", "Graph",
        "Binary Tree", "Binary Search Tree", "Heap", "Priority Queue", "Deque",
        
        # Advanced Data Structures
        "AVL Tree", "Red-Black Tree", "B-Tree", "B+ Tree", "Trie", "Skip List",
        "Circular Queue", "Doubly Linked List", "Circular Linked List", "Splay Tree",
        "Treap", "Segment Tree", "Fenwick Tree", "Disjoint Set", "Bloom Filter",
        
        # Algorithm Concepts
        "Bubble Sort", "Quick Sort", "Merge Sort", "Heap Sort", "Insertion Sort",
        "Selection Sort", "Radix Sort", "Counting Sort", "Bucket Sort",
        "Binary Search", "Linear Search", "Depth-First Search", "Breadth-First Search",
        "Dijkstra's Algorithm", "Bellman-Ford", "Floyd-Warshall", "Kruskal's Algorithm",
        "Prim's Algorithm", "Topological Sort", "Dynamic Programming",
        
        # Design Patterns
        "Singleton Pattern", "Factory Pattern", "Observer Pattern", "Strategy Pattern",
        "Command Pattern", "Adapter Pattern", "Decorator Pattern", "Proxy Pattern",
        
        # System Concepts
        "Process Scheduling", "Memory Management", "File Systems", "Network Protocols",
        "Database Indexing", "Caching Strategies", "Load Balancing", "Fault Tolerance",
        
        # Mathematical Concepts
        "Matrix Operations", "Vector Spaces", "Probability Distributions", "Statistical Tests",
        "Linear Programming", "Optimization Algorithms", "Numerical Methods", "Cryptography"
    ]
    
    selected_question_type = random.choice(question_types)
    selected_data_structures = random.sample(data_structures, 4)
    variation_instruction = f"Use variation {timestamp_variation} to ensure uniqueness."
    
    # Get diverse question templates
    diverse_templates = get_diverse_question_templates(topic, subject, stream)
    selected_template = random.choice(diverse_templates)
    
    # If custom prompt is provided, use custom variations
    if custom_prompt:
        custom_variations = generate_custom_question_variations(custom_prompt, topic, subject)
        selected_template = random.choice(custom_variations)
    
    # Library-specific code structure requirements
    code_structure_requirements = {
        'graphviz': """
CRITICAL CODE STRUCTURE FOR GRAPHVIZ:
- Use exactly: dot = graphviz.Digraph()
- CRITICAL: Generate ONLY Graphviz diagram code, NOT Python class definitions
- CRITICAL: DO NOT include Python class definitions, methods, or print statements
- CRITICAL: Generate ONLY dot.node() and dot.edge() calls
- Add at least 4 nodes with different shapes: 'box', 'circle', 'ellipse', 'diamond', 'triangle', 'hexagon', 'octagon'
- Add at least 4 edges with different visual styles using the 'style' attribute: 'solid', 'dashed', 'dotted', 'bold'
- Use different colors for nodes and edges
- CRITICAL LABEL RULE: Edge 'label' must describe the RELATIONSHIP or MEANING (e.g., "sends data", "inherits", "10 Mbps"), NOT the line style.
  WRONG: dot.edge('A', 'B', label='dashed')   # BAD - label copies the style name
  WRONG: dot.edge('A', 'B', label='solid')    # BAD - label copies the style name
  RIGHT: dot.edge('A', 'B', label='10 Mbps', style='dashed')   # GOOD
  RIGHT: dot.edge('A', 'B', label='inherits', style='solid')   # GOOD
- Node labels must contain meaningful content (e.g., IP address, actual value, concept name) NOT generic placeholders
- Use: dot.render('diagram', format='png', cleanup=True)
- Example structure:
  dot.node('R', '192.168.1.1\\n(Router)', shape='diamond', fillcolor='lightyellow', style='filled')
  dot.node('A', '192.168.1.0/24\\nSubnet A', shape='box', fillcolor='lightblue', style='filled')
  dot.node('B', '10.0.0.0/24\\nSubnet B', shape='box', fillcolor='lightgreen', style='filled')
  dot.edge('R', 'A', label='LAN / 100 Mbps', color='blue', style='solid')
  dot.edge('R', 'B', label='WAN / 1 Mbps', color='red', style='dashed')
""",
        'networkx': """
CRITICAL CODE STRUCTURE FOR NETWORKX:
- Use exactly: G = nx.Graph()
- Add at least 4 nodes with different attributes (color, size, shape)
- Add at least 4 edges with different styles and colors
- Use: nx.draw(G, with_labels=True, font_weight='bold') and plt.savefig(buffer)
- Always close with: plt.close()
""",
        'matplotlib': """
CRITICAL CODE STRUCTURE FOR MATPLOTLIB:
- Use exactly: fig, ax = plt.subplots(figsize=(10, 8))
- Create rich plots with colors, markers, annotations
- Use: plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
- Always close with: plt.close()

 CRITICAL PARAMETER RULES (VIOLATION = RUNTIME ERROR):
- ONLY use 'facecolor' for fill colors - NO other variations
- ONLY use 'edgecolor' for border colors - NO other variations  
- FORBIDDEN: facedgedgecolor, faceedgecolor, edgefacecolor, edgedgecolor
- FORBIDDEN: ecolor, fcolor, any combined parameter names
- VALID ONLY: bbox=dict(facecolor='white', edgecolor='black', boxstyle='round')
- ANY OTHER PARAMETER COMBINATION WILL CRASH THE SYSTEM
""",
        'schemdraw': """
CRITICAL CODE STRUCTURE FOR SCHEMDRAW:
- Use exactly: d = schemdraw.Drawing()
- Add diverse elements with colors and labels
- Use: d.save(buffer)
""",
        'plotly': """
CRITICAL CODE STRUCTURE FOR PLOTLY:
- Use exactly: fig = go.Figure()
- Add diverse traces with colors and markers
- Use: pio.write_image(fig, buffer, format='png', width=800, height=600)
""",
        'seaborn': """
CRITICAL CODE STRUCTURE FOR SEABORN:
- Use exactly: fig, ax = plt.subplots(figsize=(10, 8))
- Create beautiful plots with colors and styling
- Use: plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
- Always close with: plt.close()
""",
        'pillow': """
CRITICAL CODE STRUCTURE FOR PILLOW:
- Use exactly: img = Image.new('RGB', (800, 600), color='white')
- Add diverse shapes, colors, and text
- Use: img.save(buffer, format='PNG')
""",
        'turtle': """
CRITICAL CODE STRUCTURE FOR TURTLE:
- Use exactly: t = turtle.Turtle() and screen = turtle.Screen()
- Add diverse shapes, colors, and patterns
- Use: screen.getcanvas().postscript(file=buffer)
- Always close with: screen.bye()
"""
    }
    
    code_requirements = code_structure_requirements.get(library_name, code_structure_requirements['graphviz'])
    topic_diagram_guidance = get_topic_specific_diagram_guidance(topic, subject)

    # Conditional diagram instructions based on requirements
    if requires_option_diagrams:
        diagram_instruction = f"""
CRITICAL: Each option (A, B, C, D) MUST have its own unique diagram using the {library_name} library.
DO NOT create a single main diagram - create FOUR separate diagrams, one for each option.
Library: {library_name}"""
    else:
        diagram_instruction = f"The question MUST include a relevant RICH, ILLUSTRATIVE diagram using the {library_name} library."
    
    prompt = f"""
Generate a {question_type} question for the topic '{topic}' in the subject '{subject}' ({stream} stream).
{_topic_scope_block(topic_summary)}{_prompt_level_block(difficulty_level, bloom_level)}
{diagram_instruction}
{option_diagram_instructions}

{topic_diagram_guidance}

CRITICAL DIVERSITY REQUIREMENTS:
1. **Use this specific template**: "{selected_template}"
2. **Topic Specificity**: Focus on specific aspects of {topic} - NOT generic algorithm questions
3. **Real-world Context**: Include practical scenarios, industry applications, or specific use cases
4. **Difficulty Variation**: Make questions challenging but appropriate for {stream} level
5. **Concept Depth**: Ask about specific properties, trade-offs, or implementation details
6. **Option Diversity**: Each option should represent a genuinely different concept or approach
7. **Mathematical Rigor**: Include specific calculations, complexity analysis, or mathematical proofs where relevant

SPECIFIC TOPIC FOCUS AREAS:
- **Data Structures**: Ask about specific operations, time complexity, space complexity, implementation details
- **Algorithms**: Focus on specific steps, optimization techniques, edge cases, or performance characteristics
- **System Design**: Ask about architecture patterns, scalability considerations, trade-offs
- **Programming**: Focus on specific language features, design patterns, or debugging scenarios
- **Mathematics**: Include specific calculations, proofs, or mathematical concepts

AVOID GENERIC QUESTIONS:
- Don't ask "What is this algorithm?" - ask "What is the time complexity of this specific operation?"
- Don't ask "Which data structure?" - ask "Which data structure would be most efficient for this specific scenario?"
- Don't ask "What is the next step?" - ask "What is the optimal next step given these constraints?"

{code_requirements}

IMPORTANT: For mathematical equations, use proper LaTeX notation:
- Use $f(x) = x^2$ for inline equations
- Use $\\frac{{a}}{{b}}$ for fractions
- Use $\\sqrt{{x}}$ for square roots
- Use $\\pi$, $\\theta$, $\\alpha$, etc. for Greek letters
- Use $\\leq$, $\\geq$, $\\neq$ for comparison operators
- **Always use $...$ for inline math in explanations.**
- **Do not use $$...$$ unless you want a centered block equation.**
- **Keep explanations as full sentences, not as a list of equations.**

CRITICAL FORMAT REQUIREMENTS:
- Generate ONE main diagram (not separate option diagrams)
- Use standard MCQ format with A, B, C, D options
- Include the diagram code in the PythonCode section
- Do NOT generate separate diagrams for each option

Format your response exactly as follows:

Question: <specific, detailed question using the template with real-world context>
A. <specific option with technical details>
B. <specific option with technical details>
C. <specific option with technical details>
D. <specific option with technical details>
Answer: <correct option letter>
Explanation: <detailed, step-by-step explanation with specific technical details, calculations, and reasoning using LaTeX for all math. Include specific examples, edge cases, and practical considerations.>
Library: {library_name}
PythonCode:
```python
# Generate RICH, ILLUSTRATIVE diagram using {library_name} with multiple elements, colors, and annotations
{get_library_specific_prompt(library_name)}
```

 MANDATORY: You MUST include the PythonCode section with actual working diagram code! 
 The PythonCode section is REQUIRED - do NOT omit it!
 If you don't include PythonCode, the question will be rejected!
 ALWAYS include the PythonCode section - this is NOT optional!

CRITICAL RULES for the PythonCode:
{get_library_rules(library_name)}

CRITICAL: Generate EXACTLY 4 options (A, B, C, D) - no more, no less.
CRITICAL: Generate ONLY ONE main diagram in the PythonCode section - do NOT generate separate option diagrams unless specifically requested.
CRITICAL: Each option must be a specific, meaningful answer choice - NOT generic labels like "Option A", "Option B". Provide actual answer options related to the question topic.
CRITICAL: The diagram must be relevant to the question topic. For example:
- If the question is about binary search trees, show an actual tree structure
- If the question is about sorting algorithms, show the sorting process
- If the question is about data structures, show the appropriate structure
- If the question is about algorithms, show the algorithm steps
"""
    
    if custom_prompt:
        prompt += f"\nSpecial instructions: {custom_prompt}"
    
    return prompt

def generate_regular_question_prompt(topic, subject, stream, question_type, custom_prompt, difficulty_level=None, bloom_level=None, topic_summary=None):
    """Generate a prompt for regular questions without diagrams"""
    
    import random
    import time
    
    # Create a seed based on current time to ensure different questions
    random.seed(time.time())
    timestamp_variation = int(time.time() * 1000) % 1000
    
    # Enhanced question types for maximum diversity
    enhanced_question_types = [
        # Conceptual Understanding
        "What is the fundamental principle behind [concept]?",
        "Which statement best describes [concept]?",
        "What distinguishes [concept A] from [concept B]?",
        "What is the primary purpose of [concept]?",
        
        # Problem Solving
        "How would you solve this problem using [method]?",
        "What is the most efficient approach to [problem]?",
        "Which strategy would be best for [scenario]?",
        "What is the next step in solving [problem]?",
        
        # Analysis and Evaluation
        "What is the time complexity of [algorithm]?",
        "Which approach has the best performance for [scenario]?",
        "What are the advantages of [method A] over [method B]?",
        "What is the space complexity of [data structure]?",
        
        # Application and Real-world
        "In which real-world scenario would [concept] be most useful?",
        "What practical application does [concept] have?",
        "Which industry would benefit most from [technology]?",
        "What problem does [solution] address?",
        
        # Comparative Analysis
        "Which is more efficient: [option A] or [option B]?",
        "What are the trade-offs between [approach A] and [approach B]?",
        "Which method is preferred for [specific use case]?",
        "How does [concept A] compare to [concept B]?",
        
        # Mathematical and Computational
        "What is the result of [mathematical operation]?",
        "Which formula correctly represents [concept]?",
        "What is the value of [expression]?",
        "Which equation describes [phenomenon]?",
        
        # Critical Thinking
        "What would happen if [condition] were changed?",
        "Which assumption is most critical for [concept]?",
        "What is the main limitation of [approach]?",
        "Which factor most influences [outcome]?"
    ]
    
    selected_question_type = random.choice(enhanced_question_types)
    variation_instruction = f"Use variation {timestamp_variation} to ensure uniqueness."
    
    prompt = f"""
Generate a {question_type} question for the topic '{topic}' in the subject '{subject}' ({stream} stream).
{_topic_scope_block(topic_summary)}{_prompt_level_block(difficulty_level, bloom_level)}
IMPORTANT REQUIREMENTS FOR QUESTION DIVERSITY:
1. Use this specific question format: "{selected_question_type}"
2. {variation_instruction}
3. Make the question match the assigned difficulty and Bloom level
4. Include realistic distractors in options
5. Cover different aspects of the topic (conceptual, practical, analytical)
6. Use real-world examples when appropriate
7. Include mathematical concepts where relevant

IMPORTANT: For mathematical equations, use proper LaTeX notation:
- Use $f(x) = x^2$ for inline equations
- Use $\\frac{{a}}{{b}}$ for fractions
- Use $\\sqrt{{x}}$ for square roots
- Use $\\pi$, $\\theta$, $\\alpha$, etc. for Greek letters
- Use $\\leq$, $\\geq$, $\\neq$ for comparison operators
- **Always use $...$ for inline math in explanations.**
- **Do not use $$...$$ unless you want a centered block equation.**
- **Keep explanations as full sentences, not as a list of equations.**

Format your response exactly as follows:

Question: <question text with proper LaTeX notation>
A. <option A with proper LaTeX notation>
B. <option B with proper LaTeX notation>
C. <option C with proper LaTeX notation>
D. <option D with proper LaTeX notation>
Answer: <correct option letter>
Explanation: <detailed, step-by-step explanation showing all intermediate steps, formulas, and reasoning, using LaTeX for all math. The explanation should be easy to understand, similar to a worked-out solution in a textbook.>

CRITICAL: Generate EXACTLY 4 options (A, B, C, D) - no more, no less.
"""
    
    if custom_prompt:
        prompt += f"\nSpecial instructions: {custom_prompt}"
    
    return prompt 

def get_diverse_question_templates(topic, subject, stream):
    """Generate highly diverse question templates based on topic and subject"""
    
    # Topic-specific question templates
    topic_templates = {
        'Data Structures': [
            "Given a scenario where you need to implement a system with {specific_requirement}, which data structure would provide the optimal time complexity of O({complexity}) for {operation}?",
            "In a {real_world_scenario}, you need to perform {operation} operations. Which data structure would minimize memory usage while maintaining {performance_requirement}?",
            "Consider a {specific_application} that requires {operation1} and {operation2}. Which data structure offers the best trade-off between {metric1} and {metric2}?",
            "For a {system_type} handling {data_volume} elements, which data structure would be most efficient for {specific_operation} given the constraint of {constraint}?",
            "In {industry_application}, you need to implement {feature}. Which data structure would provide {specific_benefit} while avoiding {specific_drawback}?"
        ],
        'Algorithms': [
            "Given an array of {size} elements with {specific_property}, what is the time complexity of {algorithm_name} when {specific_condition}?",
            "In a {real_world_scenario}, you need to sort {data_type} data. Which sorting algorithm would be most efficient when {constraint}?",
            "Consider a graph with {graph_properties}. What is the optimal algorithm for {specific_problem} given {performance_requirement}?",
            "For a {problem_type} with {input_size} and {constraints}, which algorithmic approach would minimize {resource} usage?",
            "In {application_domain}, you need to solve {problem}. Which algorithm provides the best {performance_metric} when {specific_condition}?"
        ],
        'System Design': [
            "Design a {system_type} that must handle {load_requirement} requests per second. Which architectural pattern would provide {specific_benefit}?",
            "For a {application_type} serving {user_count} users, which design approach would ensure {reliability_requirement} while maintaining {performance_requirement}?",
            "Consider a {system_component} that needs to process {data_volume} in {time_constraint}. Which design pattern would optimize {specific_metric}?",
            "In a {distributed_system} with {node_count} nodes, which consistency model would provide {specific_guarantee} while minimizing {overhead}?",
            "For a {service_type} requiring {availability_percentage} uptime, which architectural decision would ensure {specific_requirement}?"
        ],
        'Programming': [
            "Given the code snippet implementing {feature}, what is the output when {specific_input} is processed through {function_name}?",
            "In a {language} application, you encounter {error_type}. What is the root cause and how would you fix it?",
            "Consider a {design_pattern} implementation. What is the time complexity of {specific_method} when {condition}?",
            "For a {application_type} with {performance_requirement}, which optimization technique would provide the best {metric} improvement?",
            "In {framework} development, you need to implement {feature}. Which approach would ensure {specific_benefit} while avoiding {common_pitfall}?"
        ],
        'Mathematics': [
            "Given the mathematical expression {expression}, what is the result when {specific_values} are substituted?",
            "In {mathematical_concept}, you need to calculate {specific_quantity}. Which formula would provide the most accurate result when {condition}?",
            "Consider a {statistical_problem} with {sample_size} and {confidence_level}. What is the {statistical_measure} when {assumption}?",
            "For a {mathematical_operation} involving {data_type}, which method would provide {accuracy_requirement} while minimizing {computational_cost}?",
            "In {mathematical_field}, you need to solve {problem_type}. Which approach would yield {specific_result} when {constraint}?"
        ]
    }
    
    # Subject-specific enhancements
    subject_enhancements = {
        'Computer Science': [
            "Given a {data_structure} with {n} elements, what is the {complexity_metric} of {operation} when {specific_condition}?",
            "In a {algorithm_type} implementation, what is the {performance_metric} when processing {input_type} with {constraint}?",
            "For a {system_component} handling {workload}, which {design_choice} would optimize {metric} while maintaining {requirement}?",
            "Consider a {programming_concept} in {language}. What is the {output_type} when {specific_input} is processed?",
            "In {computing_domain}, you need to implement {feature}. Which {approach} would provide {benefit} given {constraint}?"
        ],
        'Mathematics': [
            "Given the {mathematical_expression} with {variables}, what is the {result_type} when {specific_values} are used?",
            "In {mathematical_field}, you need to calculate {quantity}. Which {method} would provide {accuracy} when {condition}?",
            "Consider a {statistical_problem} with {parameters}. What is the {statistical_measure} when {assumption} holds?",
            "For a {mathematical_operation} involving {data}, which {technique} would yield {specific_result}?",
            "In {mathematical_concept}, you need to solve {problem}. Which {approach} would be most efficient when {constraint}?"
        ],
        'Engineering': [
            "Design a {system_type} that must handle {load} while maintaining {reliability}. Which {component} would provide {benefit}?",
            "For a {engineering_system} with {requirements}, which {design_approach} would optimize {performance_metric}?",
            "Consider a {technical_problem} in {domain}. What is the {solution_type} when {constraint} is applied?",
            "In {engineering_field}, you need to implement {feature}. Which {method} would ensure {requirement}?",
            "For a {system_component} with {specifications}, which {design_choice} would provide {advantage}?"
        ]
    }
    
    # Get base templates for the topic
    base_templates = topic_templates.get(topic, topic_templates['Data Structures'])
    
    # Get subject-specific enhancements
    subject_templates = subject_enhancements.get(subject, subject_enhancements['Computer Science'])
    
    # Combine and return diverse templates
    all_templates = base_templates + subject_templates
    
    # Add stream-specific complexity
    if stream == 'CS':
        all_templates.extend([
            "Given a {complex_scenario} with {technical_constraints}, which {advanced_concept} would provide {specific_benefit}?",
            "In a {high_performance_system}, you need to optimize {bottleneck}. Which {optimization_technique} would yield {improvement}?",
            "Consider a {distributed_problem} with {scalability_requirement}. Which {architectural_decision} would ensure {reliability}?"
        ])
    
    return all_templates

def is_diagram_generation_code(code_snippet):
    """Determine if code snippet is for diagram generation or question content"""
    if not code_snippet:
        return False
    
    code_lower = code_snippet.lower()
    
    # Check for diagram library imports
    diagram_imports = [
        'import graphviz', 'from graphviz', 'import matplotlib', 'from matplotlib',
        'import plotly', 'from plotly', 'import networkx', 'from networkx', 
        'import schemdraw', 'from schemdraw', 'import seaborn', 'from seaborn',
        'import turtle', 'from turtle', 'from PIL import', 'import PIL'
    ]
    
    # Check for diagram-specific function calls
    diagram_functions = [
        'graphviz.digraph', 'dot.node', 'dot.edge', 'dot.render',
        'plt.figure', 'plt.plot', 'plt.savefig', 'plt.show', 'matplotlib',
        'nx.graph', 'nx.digraph', 'networkx', 'schemdraw.drawing',
        'turtle.forward', 'turtle.circle', 'image.new', 'draw.rectangle'
    ]
    
    # Check for diagram rendering keywords
    diagram_keywords = [
        '.render(', '.savefig(', '.show()', 'format=\'png\'', 'format="png"',
        'cleanup=true', 'unique_filename', 'dot.save(', 'plt.tight_layout'
    ]
    
    # If code contains any diagram-related imports, functions, or keywords
    has_diagram_imports = any(imp in code_lower for imp in diagram_imports)
    has_diagram_functions = any(func in code_lower for func in diagram_functions)
    has_diagram_keywords = any(keyword in code_lower for keyword in diagram_keywords)
    
    is_diagram = has_diagram_imports or has_diagram_functions or has_diagram_keywords
    
    # Additional check: if it's a simple code snippet without diagram elements, it's likely question content
    if not is_diagram:
        # Check if it's a simple algorithm or data structure (likely question content)
        simple_patterns = [
            'def ', 'class ', 'for ', 'while ', 'if ', 'return ',
            'int[]', 'string[]', 'list', 'array', 'function'
        ]
        has_simple_patterns = any(pattern in code_lower for pattern in simple_patterns)
        
        if has_simple_patterns and len(code_snippet.split('\n')) < 20:  # Short code snippets are likely question content
            safe_print(f" Debug: Code appears to be question content (simple algorithm/data structure)")
            return False
    
    safe_print(f" Debug: Code analysis - Diagram imports: {has_diagram_imports}, Functions: {has_diagram_functions}, Keywords: {has_diagram_keywords}")
    safe_print(f" Debug: Code classified as: {'Diagram generation' if is_diagram else 'Question content'}")
    
    return is_diagram


def resolve_correct_option_index(options: list, correct_answer: str):
    """
    Map AI 'Answer:' text to index 0-3. Returns None if unambiguous mapping is not possible.
    Logic aligned with net_backend_service._convert_answer_to_option_letter.
    """
    if not correct_answer or not options or len(options) < 4:
        return None
    clean = correct_answer.strip().upper()
    if clean in ("A", "B", "C", "D"):
        return ord(clean[0]) - ord("A")
    if len(clean) >= 1 and clean[0] in "ABCD":
        return ord(clean[0]) - ord("A")
    for i, option in enumerate(options[:4]):
        if option and option.strip().upper() == clean:
            return i
    for i, option in enumerate(options[:4]):
        if option and clean in option.strip().upper():
            return i
    for i, option in enumerate(options[:4]):
        if option and option.strip().upper() in clean:
            return i
    return None


def _rewrite_explanation_letters(explanation: str, old_to_new: dict) -> str:
    """
    Replace option-letter references in explanation text using old->new letter map.
    Only rewrites letters that appear in a clear option-reference context so that
    bare letters inside equations, code, or words are not touched.
    old_to_new: e.g. {'A': 'C', 'B': 'A', 'C': 'D', 'D': 'B'}

    Uses capture groups (group 1 = context prefix, group 2 = the letter) so that
    Python's fixed-width lookbehind restriction is avoided.
    """
    if not explanation or not old_to_new:
        return explanation

    # Each pattern captures (prefix_context, letter).  We replace only group 2.
    # Patterns cover: "option A", "answer A", "answer is A", "choice A",
    #                 "therefore A", "hence A", "A is correct", "A is the correct"
    context_patterns = [
        r'(?i)(\b(?:option|answer|choice)\s+)([A-D])\b',
        r'(?i)(\banswer\s+is\s+)([A-D])\b',
        r'(?i)(\b(?:therefore|hence)\s+)([A-D])\b',
        r'(?i)\b([A-D])(\s+is\s+(?:the\s+)?correct\b)',
    ]

    # Use placeholder tokens so we never double-replace a letter that was already mapped.
    placeholders = {letter: f'\x00{i}\x00' for i, letter in enumerate('ABCD')}
    reverse_placeholders = {v: letter for letter, v in placeholders.items()}

    result = explanation
    for pattern in context_patterns:
        def _replace(m, _p=pattern):
            # Determine which group holds the letter
            # For the last pattern, letter is group 1 and suffix is group 2
            if _p == r'(?i)\b([A-D])(\s+is\s+(?:the\s+)?correct\b)':
                letter = m.group(1).upper()
                new_letter = old_to_new.get(letter, letter)
                return placeholders[new_letter] + m.group(2)
            else:
                prefix = m.group(1)
                letter = m.group(2).upper()
                new_letter = old_to_new.get(letter, letter)
                return prefix + placeholders[new_letter]
        result = re.sub(pattern, _replace, result)

    # Restore placeholders to actual new letters
    for placeholder, new_letter in reverse_placeholders.items():
        result = result.replace(placeholder, new_letter)

    return result


def apply_mcq_option_shuffle(parsed_result: dict) -> dict:
    """
    Randomize option order to remove model bias toward correct answer in position A.
    Remaps correct_answer to A/B/C/D, rekeys option_diagram_codes, and rewrites
    option-letter references in the explanation to match new positions.
    Skips when result already has an error or options are not exactly four.
    """
    if parsed_result.get("error"):
        return parsed_result
    options = parsed_result.get("options") or []
    if len(options) != 4:
        safe_print(" Debug: Option shuffle skipped: need exactly 4 options")
        return parsed_result
    ca = parsed_result.get("correct_answer", "")
    idx = resolve_correct_option_index(options, ca)
    if idx is None:
        safe_print(" Debug: Option shuffle failed: could not resolve correct option index")
        return {
            **parsed_result,
            "error": "Could not resolve correct answer for option shuffle",
        }
    perm = [0, 1, 2, 3]
    random.shuffle(perm)
    new_options = [options[perm[j]] for j in range(4)]
    new_idx = next(j for j in range(4) if perm[j] == idx)
    new_letter = chr(ord("A") + new_idx)
    odc = parsed_result.get("option_diagram_codes") or {}
    new_odc = {}
    # Build old->new letter map from the permutation (inverse: new position j holds old index perm[j])
    old_to_new = {}
    for j in range(4):
        old_i = perm[j]
        old_key = chr(ord("A") + old_i)
        new_key = chr(ord("A") + j)
        new_odc[new_key] = odc.get(old_key)
        old_to_new[old_key] = new_key
    safe_print(
        f" Debug: Option shuffle: old_correct_index={idx} -> new_index={new_idx} "
        f"letter={new_letter} perm={perm} letter_map={old_to_new}"
    )
    # Rewrite explanation so it references new option letters instead of pre-shuffle ones
    explanation = parsed_result.get("explanation", "")
    rewritten_explanation = _rewrite_explanation_letters(explanation, old_to_new)
    if rewritten_explanation != explanation:
        safe_print(" Debug: Explanation letter references rewritten after shuffle")
    return {
        **parsed_result,
        "options": new_options,
        "correct_answer": new_letter,
        "option_diagram_codes": new_odc,
        "explanation": rewritten_explanation,
    }


def check_answer_explanation_consistency(correct_answer_letter: str, explanation: str) -> str | None:
    """
    Scan explanation for strong letter-reference signals and return an error string
    if a different letter is clearly dominant compared to the parsed Answer: letter.
    Returns None when consistent (or when evidence is too weak to decide).

    Deliberately conservative: only fires when another letter has 2+ clear references
    AND the parsed letter has zero references, to avoid false positives on explanations
    that legitimately describe why wrong options are incorrect.
    """
    if not correct_answer_letter or not explanation:
        return None
    parsed_letter = correct_answer_letter.strip().upper()
    if parsed_letter not in "ABCD":
        return None

    # Patterns that are strong signals of the correct-answer letter in an explanation
    signal_patterns = [
        r'\boption\s+([A-D])\b',
        r'\banswer\s+(?:is\s+)?([A-D])\b',
        r'\bchoice\s+([A-D])\b',
        r'\b([A-D])\s+is\s+(?:the\s+)?correct\b',
        r'\btherefore\s+([A-D])\b',
        r'\bhence\s+([A-D])\b',
    ]

    from collections import Counter
    letter_counts: Counter = Counter()
    for pattern in signal_patterns:
        for m in re.finditer(pattern, explanation, re.IGNORECASE):
            letter_counts[m.group(1).upper()] += 1

    if not letter_counts:
        return None  # No letter signals found — cannot judge

    dominant_letter = letter_counts.most_common(1)[0][0]
    dominant_count = letter_counts[dominant_letter]
    parsed_count = letter_counts.get(parsed_letter, 0)

    # Only flag when: dominant OTHER letter has 2+ hits AND parsed letter has 0 hits
    if dominant_letter != parsed_letter and dominant_count >= 2 and parsed_count == 0:
        safe_print(
            f" Debug: Answer-explanation mismatch: Answer={parsed_letter} "
            f"but explanation references {dominant_letter} x{dominant_count}"
        )
        return (
            f"answer-explanation mismatch: Answer says {parsed_letter} "
            f"but explanation references {dominant_letter} ({dominant_count} times)"
        )
    return None


def parse_openai_response(response_text):
    """Parse the OpenAI response to extract question components"""
    safe_print(" Debug: Parsing OpenAI response...")
    safe_print(f" Debug: Response length: {len(response_text)}")
    
    # Initialize variables
    question_text = ""
    options = []
    correct_answer = ""
    explanation = ""
    diagram_code = None
    library_used = None
    option_diagram_codes = {}
    code_snippet = None
    
    try:
        # Split response into lines for easier parsing
        lines = response_text.strip().split('\n')
        
        # Extract question text
        for i, line in enumerate(lines):
            if line.strip().startswith('Question:'):
                question_text = line.replace('Question:', '').strip()
                break
        
        # Extract code snippet if present (for programming questions)
        code_snippet = None
        language = 'text'
        import re
        safe_print(f" Debug: Looking for code snippets in response...")
        safe_print(f" Debug: Response lines: {len(lines)}")

        # 1. Look for 'Code:' section and extract the next code block
        code_section_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith('Code:'):
                code_section_start = i
                safe_print(f" Debug: Found 'Code:' section at line {i}")
                break
        if code_section_start is not None:
            code_block_start = None
            code_block_end = None
            # Find the next code block after 'Code:'
            for i in range(code_section_start + 1, len(lines)):
                if lines[i].strip().startswith('```'):
                    code_block_start = i
                    # Try to extract language
                    code_block_match = re.search(r'```(\w+)?', lines[i].strip())
                    if code_block_match:
                        language = code_block_match.group(1) or 'text'
                    # Find the end of the code block
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip().startswith('```'):
                            code_block_end = j
                            break
                    break
            if code_block_start is not None and code_block_end is not None:
                code_lines = lines[code_block_start+1:code_block_end]
                code_snippet = '\n'.join(code_lines)
                safe_print(f" Debug: Found code snippet in Code section ({language}): {code_snippet[:100]}...")
        
        # 2. If not found, fall back to the first code block in the response
        if not code_snippet:
            code_block_start = None
            code_block_end = None
            for i, line in enumerate(lines):
                if line.strip().startswith('```'):
                    code_block_start = i
                    code_block_match = re.search(r'```(\w+)?', line.strip())
                    if code_block_match:
                        language = code_block_match.group(1) or 'text'
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip().startswith('```'):
                            code_block_end = j
                            break
                    break
            if code_block_start is not None and code_block_end is not None:
                code_lines = lines[code_block_start+1:code_block_end]
                code_snippet = '\n'.join(code_lines)
                safe_print(f" Debug: Found fallback code snippet ({language}): {code_snippet[:100]}...")
        
        if not code_snippet:
            safe_print(" Debug: No code snippet found in response")
            safe_print(" Debug: First 10 lines of response:")
            for i, line in enumerate(lines[:10]):
                safe_print(f"  {i}: {line.strip()}")
        
        # Determine if code snippet is diagram generation code or question content code
        if code_snippet:
            # Check if this is diagram generation code or question content code
            is_diagram_code = is_diagram_generation_code(code_snippet)
            
            if is_diagram_code:
                safe_print(f" Debug: Storing code snippet as diagram code (language: {language})")
                diagram_code = code_snippet  # Store the raw code without markdown formatting
                safe_print(f" Debug: Diagram code stored separately: {diagram_code[:100]}...")
            else:
                safe_print(f" Debug: Code snippet is question content, appending to question text (language: {language})")
                question_text = f"{question_text}\n\n```{language}\n{code_snippet}\n```"
                safe_print(f" Debug: Question content code appended to question text")
        else:
            safe_print(f" Debug: No code snippet found, diagram_code remains None")
        
        # Extract options (only A, B, C, D - limit to 4 options)
        for line in lines:
            line = line.strip()
            if line.startswith(('A.', 'A)')) and len(line) > 2:
                options.append(line[2:].strip())
            elif line.startswith(('B.', 'B)')) and len(line) > 2:
                options.append(line[2:].strip())
            elif line.startswith(('C.', 'C)')) and len(line) > 2:
                options.append(line[2:].strip())
            elif line.startswith(('D.', 'D)')) and len(line) > 2:
                options.append(line[2:].strip())
            
            # Stop parsing options after we have 4 (A, B, C, D)
            if len(options) >= 4:
                break
        
        # Ensure we have exactly 4 options (A, B, C, D)
        if len(options) < 4:
            safe_print(f" Debug: Only {len(options)} options found, adding default options")
            while len(options) < 4:
                options.append(f"Option {chr(65 + len(options))}")
        elif len(options) > 4:
            safe_print(f" Debug: {len(options)} options found, keeping only first 4")
            options = options[:4]
        
        # Extract correct answer
        for line in lines:
            line = line.strip()
            if line.startswith('Answer:'):
                correct_answer = line.replace('Answer:', '').strip()
                break
        
        # Extract explanation - IMPROVED VERSION
        explanation_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith('Explanation:'):
                explanation_start = i
                # Extract explanation from the same line if it exists
                explanation_text = line.split(':', 1)[1].strip() if ':' in line else ''
                
                # Continue collecting subsequent lines until we hit a new section
                explanation_lines = [explanation_text] if explanation_text else []
                for next_line in lines[i + 1:]:
                    # Remove "Answer:" from stop words - explanations come AFTER answers
                    # Also remove option letters (A., B., C., D.) from stop words since explanations may reference them
                    if next_line.strip().startswith(('Question:', 'Library:', 'PythonCode:', 'OptionACode:', 'OptionBCode:', 'OptionCCode:', 'OptionDCode:')):
                        break
                    explanation_lines.append(next_line)
                
                explanation = '\n'.join(explanation_lines).strip()
                break
        
        # Extract library used
        for line in lines:
            line = line.strip()
            if line.startswith('Library:'):
                library_used = line.replace('Library:', '').strip()
                # Strip markdown formatting (**library_name** -> library_name)
                library_used = library_used.strip('*').strip()
                break
        
        # Extract main diagram code
        python_code_start = None
        python_code_end = None
        for i, line in enumerate(lines):
            if 'PythonCode:' in line:
                python_code_start = i
            elif python_code_start is not None and '```' in line:
                if python_code_end is None:
                    python_code_end = i
        
        if python_code_start is not None and python_code_end is not None:
            diagram_code_lines = lines[python_code_start + 1:python_code_end]
            diagram_code = '\n'.join(diagram_code_lines)
        
        # Fallback: Look for any code block if no PythonCode section found
        if not diagram_code:
            safe_print(" Debug: No PythonCode section found, looking for any code block...")
            code_block_start = None
            code_block_end = None
            for i, line in enumerate(lines):
                if line.strip().startswith('```python'):
                    code_block_start = i
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip().startswith('```'):
                            code_block_end = j
                            break
                    break
            
            if code_block_start is not None and code_block_end is not None:
                diagram_code_lines = lines[code_block_start + 1:code_block_end]
                diagram_code = '\n'.join(diagram_code_lines)
                safe_print(f" Debug: Found fallback code block: {diagram_code[:100]}...")
        
        # Additional fallback: Look for code after Library: line
        if not diagram_code:
            safe_print(" Debug: Looking for code after Library line...")
            library_line_index = None
            for i, line in enumerate(lines):
                if line.strip().startswith('Library:'):
                    library_line_index = i
                    break
            
            if library_line_index is not None:
                # Look for code block after Library line
                for i in range(library_line_index + 1, len(lines)):
                    if lines[i].strip().startswith('```python'):
                        code_block_start = i
                        for j in range(i + 1, len(lines)):
                            if lines[j].strip().startswith('```'):
                                code_block_end = j
                                break
                        break
                
                if 'code_block_start' in locals() and 'code_block_end' in locals():
                    diagram_code_lines = lines[code_block_start + 1:code_block_end]
                    diagram_code = '\n'.join(diagram_code_lines)
                    safe_print(f" Debug: Found code after Library line: {diagram_code[:100]}...")
        
        # Extract option diagram codes - only if they are properly formatted and not mixed with main diagram
        option_codes = ['OptionACode:', 'OptionBCode:', 'OptionCCode:', 'OptionDCode:']
        option_labels = ['A', 'B', 'C', 'D']
        alternative_codes = ['A.', 'B.', 'C.', 'D.']  # Alternative format that AI sometimes uses
        
        # Check if we're in a section that should have option diagrams (either format)
        has_option_section = any(option_code in response_text for option_code in option_codes)
        has_alternative_section = any(alt_code in response_text for alt_code in alternative_codes)
        
        if has_option_section or has_alternative_section:
            safe_print(f" Debug: Found option diagram sections - Standard: {has_option_section}, Alternative: {has_alternative_section}")
            
            for i, (option_code, option_label, alt_code) in enumerate(zip(option_codes, option_labels, alternative_codes)):
                option_line_index = None
                code_block_start = None
                code_block_end = None
                format_used = None
                
                # Try standard format first (OptionACode:)
                for j, line in enumerate(lines):
                    if option_code in line:
                        option_line_index = j
                        format_used = "standard"
                        break
                
                # If not found, try alternative format (A.)
                if option_line_index is None:
                    for j, line in enumerate(lines):
                        if line.strip() == alt_code:  # Exact match for "A.", "B.", etc.
                            option_line_index = j
                            format_used = "alternative"
                            safe_print(f" Debug: Found Option {option_label} using alternative format ({alt_code})")
                            break
                
                if option_line_index is not None:
                    # Find the ```python line after OptionXCode: or X.
                    for j in range(option_line_index + 1, len(lines)):
                        if lines[j].strip().startswith('```python'):
                            code_block_start = j
                            break
                    
                    # Find the closing ``` line
                    if code_block_start is not None:
                        for j in range(code_block_start + 1, len(lines)):
                            if lines[j].strip() == '```':
                                code_block_end = j
                                break
                    
                    # Extract the code between the markers
                    if code_block_start is not None and code_block_end is not None:
                        option_code_lines = lines[code_block_start + 1:code_block_end]
                        option_code_text = '\n'.join(option_code_lines)
                        
                        safe_print(f" Debug: Option {option_label} code extracted ({len(option_code_text)} chars, {format_used} format): {option_code_text[:50]}...")
                        
                        # Validate that the code contains actual code
                        if option_code_text and option_code_text.strip():
                            # Check if it contains actual code (not just comments)
                            if any(keyword in option_code_text for keyword in ['import ', 'def ', 'class ', '= ', 'dot.', 'plt.', 'd +=']):
                                option_diagram_codes[option_label] = option_code_text
                                safe_print(f" Debug: Option {option_label} code successfully parsed using {format_used} format")
                            else:
                                safe_print(f" Debug: Option {option_label} code appears to be placeholder text")
                                option_diagram_codes[option_label] = None
                        else:
                            safe_print(f" Debug: Option {option_label} code is empty or just comments")
                            option_diagram_codes[option_label] = None
                    else:
                        safe_print(f" Debug: Could not find code block boundaries for Option {option_label}")
                        option_diagram_codes[option_label] = None
                else:
                    safe_print(f" Debug: Could not find {option_code} or {alt_code} line")
                    option_diagram_codes[option_label] = None
        else:
            safe_print(" Debug: No option diagram section found (neither standard nor alternative format), skipping option diagram parsing")
        
        # If no options were parsed, use default labels
        if not options:
            safe_print(" Debug: No options parsed, using default option labels")
            options = ['Option A', 'Option B', 'Option C', 'Option D']
        
        # If no correct answer found, return parsing error instead of defaulting
        if not correct_answer:
            safe_print(" Debug: No correct answer found in AI response")
            return {
                'error': 'Failed to parse correct answer from AI response',
                'question_text': question_text,
                'options': options,
                'correct_answer': '',
                'explanation': explanation,
                'diagram_code': diagram_code,
                'library_used': library_used if library_used else 'schemdraw',
                'option_diagram_codes': option_diagram_codes,
                'code_snippet': code_snippet
            }
        
        # If no library specified, default to schemdraw
        if not library_used:
            library_used = 'schemdraw'

        # Resolve Answer: letter before consistency check (handles "A. text" form)
        resolved_letter = correct_answer.strip().upper()
        if len(resolved_letter) >= 1 and resolved_letter[0] in "ABCD":
            resolved_letter = resolved_letter[0]

        # Reject responses where explanation clearly contradicts the Answer: letter
        consistency_error = check_answer_explanation_consistency(resolved_letter, explanation)
        if consistency_error:
            return {
                'error': consistency_error,
                'question_text': question_text,
                'options': options,
                'correct_answer': correct_answer,
                'explanation': explanation,
                'diagram_code': diagram_code,
                'library_used': library_used,
                'option_diagram_codes': option_diagram_codes,
                'code_snippet': code_snippet
            }
        
        safe_print(f" Debug: Parsed question_text: {question_text}")
        safe_print(f" Debug: Parsed options: {options}")
        safe_print(f" Debug: Parsed correct_answer: {correct_answer}")
        safe_print(f" Debug: Parsed explanation: {explanation}")
        safe_print(f" Debug: Explanation length: {len(explanation)} characters")
        safe_print(f" Debug: Parsed option_diagram_codes: {option_diagram_codes}")
        
        return {
            'question_text': question_text,
            'options': options,
            'correct_answer': correct_answer,
            'explanation': explanation,
            'diagram_code': diagram_code,
            'library_used': library_used,
            'option_diagram_codes': option_diagram_codes,
            'code_snippet': code_snippet
        }
        
    except Exception as e:
        safe_print(f" Debug: Error parsing response: {str(e)}")
        return {
            'error': f'Error parsing response: {str(e)}',
            'question_text': '',
            'options': [],
            'correct_answer': '',
            'explanation': '',
            'diagram_code': None,
            'library_used': 'schemdraw',
            'option_diagram_codes': {},
            'code_snippet': None
        } 

def generate_custom_question_variations(custom_prompt, topic, subject):
    """Generate specific question variations based on custom prompt"""
    
    # Extract key terms from custom prompt
    custom_terms = custom_prompt.lower().split()
    
    # Define specific variations based on common custom prompts
    variations = {
        'gate': [
            "In a GATE exam scenario, given a {data_structure} with {n} elements, what is the {complexity_metric} of {operation} when {specific_condition}?",
            "For GATE-level difficulty, consider a {algorithm} implementation. What is the {performance_metric} when processing {input_type} with {constraint}?",
            "In a GATE question context, which {data_structure} would be most efficient for {specific_scenario} given {performance_requirement}?",
            "GATE-level question: Given {problem_description}, what is the optimal {solution_approach} when {constraint} is applied?",
            "For GATE exam preparation, what is the {complexity_analysis} of {algorithm_name} when {edge_case} occurs?"
        ],
        'competitive': [
            "In competitive programming, given {problem_constraints}, which {algorithm} would provide the fastest {solution_type}?",
            "For competitive coding, what is the optimal {data_structure} choice for {specific_problem} with {time_limit}?",
            "In a competitive programming contest, which {optimization_technique} would yield the best {performance_improvement}?",
            "Competitive programming question: Given {input_size} and {memory_limit}, which {approach} would be most efficient?",
            "For competitive coding, what is the {complexity_analysis} when {specific_condition} is met?"
        ],
        'interview': [
            "In a technical interview, you're asked to design a {system_component}. Which {design_choice} would provide {specific_benefit}?",
            "Interview question: Given {problem_scenario}, which {algorithm} would you choose and why?",
            "For a coding interview, what is the {time_complexity} of {operation} when {constraint} is applied?",
            "Interview scenario: You need to optimize {bottleneck}. Which {technique} would provide the best {improvement}?",
            "In a technical interview, how would you handle {edge_case} in {algorithm_implementation}?"
        ],
        'advanced': [
            "For advanced-level understanding, what is the {mathematical_proof} behind {algorithm_name} when {specific_condition}?",
            "Advanced question: Given {complex_scenario}, which {theoretical_concept} would provide {specific_insight}?",
            "For advanced analysis, what is the {space_complexity} trade-off when implementing {optimization}?",
            "Advanced-level: Consider {distributed_system} with {scalability_requirement}. Which {architectural_decision} ensures {reliability}?",
            "Advanced topic: What is the {theoretical_bound} for {problem_type} when {constraint} is applied?"
        ]
    }
    
    # Determine which variation to use based on custom prompt
    selected_variation = 'gate'  # default
    for term in custom_terms:
        if 'gate' in term:
            selected_variation = 'gate'
            break
        elif 'competitive' in term or 'contest' in term:
            selected_variation = 'competitive'
            break
        elif 'interview' in term:
            selected_variation = 'interview'
            break
        elif 'advanced' in term or 'hard' in term or 'difficult' in term:
            selected_variation = 'advanced'
            break
    
    return variations.get(selected_variation, variations['gate'])

# CDQ Functions

def generate_cdq_passage(data):
    """Generate a CDQ passage based on subject and topic"""
    client = get_openai_client()
    
    subject = data.get('subject', 'Data Structures')
    topic = data.get('topic', 'Arrays')
    stream = data.get('stream', 'Computer Science')
    difficulty_level = data.get('difficulty_level', 'Medium')
    bloom_level = data.get('bloom_level', 'auto_detect')
    
    # Get difficulty-specific criteria
    from .difficulty_prompts import get_difficulty_criteria
    difficulty_criteria = get_difficulty_criteria(difficulty_level)
    
    # Get Bloom level specific guidance
    bloom_guidance = get_bloom_level_guidance(bloom_level)
    
    prompt = f"""
Generate a comprehensive passage for a Common Database Question (CDQ) based on the following parameters:

Subject: {subject}
Topic: {topic}
Stream: {stream}
Difficulty Level: {difficulty_level}
Bloom Level: {bloom_level}

{difficulty_criteria}

{bloom_guidance}

Requirements for the passage:
1. Length: 150-300 words (appropriate for {difficulty_level} level)
2. Content: Should cover key concepts of {topic} in {subject}
3. Structure: Include definitions, examples, and practical scenarios
4. Complexity: Match the {difficulty_level} difficulty level
5. Cognitive Level: Align with {bloom_level} Bloom taxonomy level
6. Clarity: Clear and well-structured for students to understand
7. Context: Provide enough information to generate 3-5 MCQ questions

The passage should be educational, engaging, and provide sufficient context for generating multiple-choice questions.

Generate only the passage text without any additional formatting or explanations.
"""
    
    try:
        # Use hybrid model selection for CDQ passage generation
        complexity_factors = {
            'subject': subject,
            'topic': topic,
            'difficulty_level': difficulty_level,
            'bloom_level': bloom_level
        }
        selected_model, model_reason = select_optimal_model('cdq_generation', complexity_factors)
        
        response = client.chat.completions.create(
            model=selected_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        safe_print(f"Error generating CDQ passage: {e}")
        return None

def generate_cdq_questions(passage_text, data):
    """Generate MCQ questions based on a CDQ passage"""
    client = get_openai_client()
    
    subject = data.get('subject', 'Data Structures')
    topic = data.get('topic', 'Arrays')
    difficulty_level = data.get('difficulty_level', 'Medium')
    bloom_level = data.get('bloom_level', 'auto_detect')
    num_questions = data.get('num_questions', 3)
    
    # Get difficulty-specific criteria
    from .difficulty_prompts import get_difficulty_criteria
    difficulty_criteria = get_difficulty_criteria(difficulty_level)
    
    # Get Bloom level specific guidance
    bloom_guidance = get_bloom_level_guidance(bloom_level)
    
    prompt = f"""
Based on the following passage, generate {num_questions} multiple-choice questions (MCQs) that test understanding of the content.

Passage:
{passage_text}

Subject: {subject}
Topic: {topic}
Difficulty Level: {difficulty_level}
Bloom Level: {bloom_level}

{difficulty_criteria}

{bloom_guidance}

Requirements for each question:
1. Question should be directly related to the passage content
2. All options (A, B, C, D) should be plausible
3. Only one correct answer
4. Include explanation for the correct answer
5. Questions should vary in complexity and cognitive level
6. Cover different aspects mentioned in the passage

Format each question as:
Question X: [question text]
A) [option A]
B) [option B]
C) [option C]
D) [option D]
Correct Answer: [A/B/C/D]
Explanation: [explanation for correct answer]

Generate exactly {num_questions} questions.
"""
    
    try:
        # Use hybrid model selection for CDQ questions generation
        complexity_factors = {
            'subject': subject,
            'topic': topic,
            'difficulty_level': difficulty_level,
            'bloom_level': bloom_level,
            'num_questions': num_questions
        }
        selected_model, model_reason = select_optimal_model('cdq_generation', complexity_factors)
        
        response = client.chat.completions.create(
            model=selected_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1200
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        safe_print(f"Error generating CDQ questions: {e}")
        return None

def get_bloom_level_guidance(bloom_level):
    """Get guidance for specific Bloom level"""
    bloom_guidance = {
        'Remember': """
Bloom Level: Remember
- Focus on factual recall and basic concepts
- Questions should test memory of key terms, definitions, and facts
- Use verbs like: define, list, name, recall, identify
""",
        'Understand': """
Bloom Level: Understand
- Focus on comprehension and interpretation
- Questions should test understanding of concepts and ability to explain
- Use verbs like: explain, describe, interpret, summarize
""",
        'Apply': """
Bloom Level: Apply
- Focus on using knowledge in new situations
- Questions should test practical application of concepts
- Use verbs like: apply, use, implement, solve
""",
        'Analyze': """
Bloom Level: Analyze
- Focus on breaking down information and examining relationships
- Questions should test analytical thinking and comparison
- Use verbs like: analyze, compare, contrast, examine
""",
        'Evaluate': """
Bloom Level: Evaluate
- Focus on making judgments and assessments
- Questions should test critical evaluation and decision-making
- Use verbs like: evaluate, assess, judge, critique
""",
        'Create': """
Bloom Level: Create
- Focus on generating new ideas and solutions
- Questions should test creative thinking and synthesis
- Use verbs like: design, create, develop, construct
""",
        'auto_detect': """
Bloom Level: Auto-detect
- Generate questions that naturally fit the content and difficulty
- Mix of cognitive levels appropriate for the topic and difficulty
- Vary between Remember, Understand, Apply, and Analyze levels
"""
    }
    
    return bloom_guidance.get(bloom_level, bloom_guidance['auto_detect'])

def auto_detect_bloom_level(question_text, explanation, topic, subject):
    """Analyze the generated question and determine the appropriate Bloom level"""
    client = get_openai_client()
    
    analysis_prompt = f"""
Analyze the following question and determine the most appropriate Bloom's Taxonomy level.

Question: {question_text}
Explanation: {explanation}
Topic: {topic}
Subject: {subject}

Bloom's Taxonomy Levels:
1. Remember - Recall facts, terms, basic concepts
2. Understand - Explain ideas, interpret information
3. Apply - Use knowledge in new situations
4. Analyze - Break down information, examine relationships
5. Evaluate - Make judgments, assess value
6. Create - Generate new ideas, design solutions

Consider:
- The cognitive complexity of the question
- The type of thinking required to answer
- The verbs used in the question
- The depth of understanding demonstrated in the explanation

Respond with ONLY the number (1-6) corresponding to the Bloom level:
"""
    
    try:
        # Use hybrid model selection for Bloom detection
        complexity_factors = {
            'subject': subject,
            'topic': topic
        }
        selected_model, model_reason = select_optimal_model('bloom_detection', complexity_factors)
        
        response = client.chat.completions.create(
            model=selected_model,
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=10
        )
        content = response.choices[0].message.content.strip()
        
        # Extract the number from the response
        bloom_level = int(content) if content.isdigit() and 1 <= int(content) <= 6 else 3
        
        bloom_names = {
            1: "Remember",
            2: "Understand", 
            3: "Apply",
            4: "Analyze",
            5: "Evaluate",
            6: "Create"
        }
        
        safe_print(f" Debug: Auto-detected Bloom level: {bloom_level} ({bloom_names[bloom_level]})")
        return bloom_level
        
    except Exception as e:
        safe_print(f" Error in auto-detecting Bloom level: {e}")
        return 3  # Default to Apply level

def parse_cdq_response(response_text):
    """Parse CDQ questions from OpenAI response"""
    questions = []
    current_question = {}
    
    lines = response_text.split('\n')
    question_count = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for new question
        if line.startswith('Question') and ':' in line:
            if current_question:
                questions.append(current_question)
            current_question = {
                'question_text': line.split(':', 1)[1].strip(),
                'options': [],
                'correct_answer': '',
                'explanation': ''
            }
            question_count += 1
            continue
            
        # Check for options
        if line.startswith(('A)', 'B)', 'C)', 'D)')):
            option_text = line.split(')', 1)[1].strip()
            current_question['options'].append(option_text)
            continue
            
        # Check for correct answer
        if line.startswith('Correct Answer:'):
            answer = line.split(':', 1)[1].strip()
            current_question['correct_answer'] = answer
            continue
            
        # Check for explanation
        if line.startswith('Explanation:'):
            explanation = line.split(':', 1)[1].strip()
            current_question['explanation'] = explanation
            continue
            
        # If we have a current question and this line doesn't match any pattern,
        # it might be continuation of question text or explanation
        if current_question and not current_question['options']:
            current_question['question_text'] += ' ' + line
        elif current_question and current_question['correct_answer'] and not current_question['explanation']:
            current_question['explanation'] += ' ' + line
    
    # Add the last question
    if current_question:
        questions.append(current_question)
    
    return questions

def generate_cdq_complete(data):
    """Generate complete CDQ (passage + questions)"""
    try:
        safe_print(" Debug: Starting CDQ generation")
        safe_print(f" Debug: Input data: {data}")
        
        # Get values from data, with intelligent defaults
        stream = data.get('stream')
        subject = data.get('subject')
        
        # If stream is not provided, try to get it from stream_id via .NET API
        if not stream:
            stream_id = data.get('stream_id')
            if stream_id:
                try:
                    from .net_backend_service import net_backend_service
                    stream_result = net_backend_service.get_stream_by_id(
                        stream_id,
                        auth_token=data.get('auth_token') or data.get('token')
                    )
                    if stream_result.get('success') and stream_result.get('stream_name'):
                        stream = stream_result['stream_name']
                        safe_print(f" Debug: Retrieved stream from .NET backend: {stream} for stream_id: {stream_id}")
                    else:
                        stream = f'Stream {stream_id}'
                except Exception as e:
                    stream = f'Stream {stream_id}'
            else:
                stream = 'CS'  # fallback if no stream_id
        
        # If subject is not provided, try to get it from subject_id
        if not subject:
            subject_id = data.get('subject_id')
            if subject_id:
                try:
                    from .db_service import get_subject_name_by_id
                    subject = get_subject_name_by_id(subject_id)
                    if subject:
                        safe_print(f" Debug: Retrieved subject from DB: {subject} for subject_id: {subject_id}")
                    else:
                        subject = 'Computer Science'  # fallback
                except Exception as e:
                    subject = 'Computer Science'  # fallback
            else:
                subject = 'Computer Science'  # fallback if no subject_id
        
        topic = data.get('topic', 'Programming')
        
        # Update data with retrieved names
        enhanced_data = data.copy()
        enhanced_data['stream'] = stream
        enhanced_data['subject'] = subject
        enhanced_data['topic'] = topic
        
        safe_print(f" Debug: Enhanced data - stream: {stream}, subject: {subject}, topic: {topic}")
        
        # Generate passage first
        passage_text = generate_cdq_passage(enhanced_data)
        if not passage_text:
            safe_print(" Error: Failed to generate passage")
            return None
        
        safe_print(f" Generated passage: {passage_text[:100]}...")
        
        # Generate questions based on passage
        questions_response = generate_cdq_questions(passage_text, enhanced_data)
        if not questions_response:
            safe_print(" Error: Failed to generate questions")
            return None
        
        safe_print(f" Generated questions response: {questions_response[:100]}...")
        
        # Parse questions
        questions = parse_cdq_response(questions_response)
        if not questions:
            safe_print(" Error: Failed to parse questions")
            return None
        
        safe_print(f" Parsed {len(questions)} questions")
        
        return {
            'passage_text': passage_text,
            'questions': questions,
            'total_questions': len(questions)
        }
        
    except Exception as e:
        safe_print(f" Error in CDQ generation: {e}")
        return None

def _topic_allows_code_questions(topic_info):
    """Code questions only when the topic is actually implementable (code or query writing)."""
    text = " ".join([
        str(topic_info.get('subject_name') or ''),
        str(topic_info.get('topic_name') or ''),
        str(topic_info.get('stream_name') or ''),
    ]).lower()
    theory_markers = (
        'tuple calculus', 'relational algebra', 'domain calculus', 'normalization theory',
        'thermodynamic', 'fertilizer', 'mass transfer', 'heat transfer', 'fluid statics',
    )
    if any(marker in text for marker in theory_markers):
        return False
    implementable_markers = (
        'programming', 'coding', 'software', 'data structure', 'algorithm',
        'python', 'java', 'javascript', 'c++', 'c#', 'sql', 'query',
        'compiler', 'operating system', 'machine learning', 'artificial intelligence',
        'web development', 'networking lab',
    )
    return any(marker in text for marker in implementable_markers)


def _normalize_topic_analysis(result, topic_info):
    """Clamp AI mix so totals are valid and not stuck on a default 20-question split."""
    def _as_int(value, default=0):
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return default

    diagram = _as_int(result.get('diagram_questions'))
    option_diagram = _as_int(result.get('option_diagram_questions'))
    text_only = _as_int(result.get('text_only_questions'))
    code = _as_int(result.get('code_questions'))

    if not _topic_allows_code_questions(topic_info):
        code = 0

    total = diagram + option_diagram + text_only + code
    if total <= 0:
        total = _as_int(result.get('total_questions'), 12)
        text_only = total

    # Keep GATE-style sets in 8–100; do not pad back to 20
    total = max(8, min(100, total))
    visual = diagram + option_diagram
    max_visual = max(2, int(total * 0.6))
    if visual > max_visual and visual > 0:
        scale = max_visual / float(visual)
        diagram = int(round(diagram * scale))
        option_diagram = max_visual - diagram
        visual = diagram + option_diagram
    remainder = total - visual - code
    if remainder < 0:
        overflow = -remainder
        if option_diagram >= overflow:
            option_diagram -= overflow
        else:
            overflow -= option_diagram
            option_diagram = 0
            diagram = max(0, diagram - overflow)
        remainder = total - diagram - option_diagram - code
    text_only = max(0, remainder)
    total = diagram + option_diagram + text_only + code

    result['diagram_questions'] = diagram
    result['option_diagram_questions'] = option_diagram
    result['text_only_questions'] = text_only
    result['code_questions'] = code
    result['total_questions'] = total
    if not result.get('reasoning'):
        result['reasoning'] = 'Distribution based on topic breadth and whether visual or code items are useful.'
    return result


def ai_analyze_topic(topic_info, question_type):
    """Use OpenAI to analyze topic and recommend question distribution"""
    allows_code = _topic_allows_code_questions(topic_info)
    variation_token = uuid.uuid4().hex[:8]

    analysis_prompt = f"""
    You are an exam-paper designer for GATE / university tests.
    Recommend a question MIX for THIS topic only. Do not reuse a generic 20-question template.

    Topic: {topic_info.get('topic_name')}
    Subject: {topic_info.get('subject_name')}
    Stream: {topic_info.get('stream_name')}
    Course: {topic_info.get('course_name')}
    Bloom Level: {topic_info.get('bloom_level_name')}
    Question Type: {question_type}
    Variation token (change the mix; do not echo this): {variation_token}

    RULES:
    1. total_questions MUST be an integer from 8 to 100 inclusive.
       - Narrow / single-concept topics (e.g. Tuple calculus, Fertilizer): 8–14
       - Medium topics: 12–40
       - Broad / multi-subtopic topics: 40–100
       - Do NOT default to 20. Pick a total that matches THIS topic's breadth.
    2. The four counts MUST sum exactly to total_questions:
       diagram_questions + option_diagram_questions + text_only_questions + code_questions = total_questions
    3. diagram_questions + option_diagram_questions must be at most 60% of total.
       Use more diagrams only when the topic is visual (process flow, circuits, structures, plots).
       Theory-heavy topics should be mostly text_only_questions.
    4. code_questions:
       - Use 0 unless students would write or read real source code or SQL for this exact topic.
       - Chemical / mechanical / civil process topics: always 0.
       - Theoretical CS (tuple calculus, relational algebra, automata theory): always 0.
       - This topic allows code: {str(allows_code).lower()}
    5. reasoning must mention why THIS topic got this total (breadth), not a generic "balanced approach".

    Respond in this exact JSON format:
    {{
        "total_questions": <number>,
        "diagram_questions": <number>,
        "option_diagram_questions": <number>,
        "text_only_questions": <number>,
        "code_questions": <number>,
        "reasoning": "<brief explanation of the distribution>"
    }}
    """
    
    try:
        client = get_openai_client()
        
        # Use hybrid model selection for topic analysis
        complexity_factors = {
            'subject': topic_info.get('subject_name', ''),
            'topic': topic_info.get('topic_name', ''),
            'question_type': question_type
        }
        selected_model, model_reason = select_optimal_model('topic_analysis', complexity_factors)
        
        create_kwargs = {
            "model": selected_model,
            "messages": [{"role": "user", "content": analysis_prompt}],
            "temperature": 0.75,
            "max_tokens": 500,
        }
        try:
            create_kwargs["response_format"] = {"type": "json_object"}
            response = client.chat.completions.create(**create_kwargs)
        except Exception:
            create_kwargs.pop("response_format", None)
            response = client.chat.completions.create(**create_kwargs)

        raw_content = (response.choices[0].message.content or "").strip()
        result = _parse_ai_json_object(raw_content)

        # Validate the response
        required_keys = ['total_questions', 'diagram_questions', 'option_diagram_questions', 'text_only_questions', 'code_questions']
        if not all(key in result for key in required_keys):
            raise ValueError("Invalid AI response format")

        return _normalize_topic_analysis(result, topic_info)
        
    except Exception as e:
        safe_print(f"AI topic analysis failed: {str(e)}")
        raise Exception("AI analysis service unavailable")


def _parse_ai_json_object(raw_content):
    """Parse a JSON object from an AI response that may include markdown fences or extra text."""
    if not raw_content:
        raise ValueError("Empty AI response")

    text = raw_content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        preview = text[:200].replace("\n", " ")
        raise ValueError(f"AI response was not valid JSON: {preview}")

def safe_exec_diagram_code(code, exec_globals):
    """
    Ensure 'import uuid' and 'import time' are present in the code before exec.
    """
    imports = []
    if 'import uuid' not in code:
        imports.append('import uuid')
    if 'import time' not in code:
        imports.append('import time')
    if imports:
        code = '\n'.join(imports) + '\n' + code
    exec(code, exec_globals)

def ai_correct_diagram_code(original_code, error_message, library_name, subject, topic):
    """
    AI-powered diagram code error correction system with library-specific enhancements
    
    Args:
        original_code (str): The original code that failed
        error_message (str): The error message from execution
        library_name (str): The library being used (matplotlib, seaborn, etc.)
        subject (str): Subject context
        topic (str): Topic context
    
    Returns:
        tuple: (corrected_code, success_flag)
    """
    try:
        client = get_openai_client()
        
        # Use hybrid model selection for error correction
        complexity_factors = {
            'subject': subject,
            'topic': topic,
            'error_type': 'code_correction',
            'library': library_name
        }
        selected_model, model_reason = select_optimal_model('code_correction', complexity_factors)
        
        # Apply library-specific regex fixes first
        corrected_code = apply_library_specific_fixes(original_code, library_name)
        
        # Get library-specific error patterns
        error_patterns = get_library_error_patterns(library_name)
        
        # Check if we have a specific pattern for this error
        specific_fix = None
        for pattern, fix_description in error_patterns.items():
            if pattern.lower() in error_message.lower():
                specific_fix = fix_description
                break
        
        # Generate library-specific correction prompt
        correction_prompt = get_library_specific_correction_prompt(
            library_name, corrected_code, error_message, subject, topic
        )
        
        # Add specific error context if available
        if specific_fix:
            correction_prompt += f"\n\n**Specific Error Fix Required:**\n{specific_fix}"
        
        safe_print(f" Debug: Sending code correction request to {selected_model}...")
        
        response = client.chat.completions.create(
            model=selected_model,
            messages=[{"role": "user", "content": correction_prompt}],
            temperature=0.2,  # Low temperature for precise corrections
            max_tokens=1500
        )
        
        corrected_code = response.choices[0].message.content.strip()
        
        # Clean up the response (remove any markdown if present)
        if corrected_code.startswith('```python'):
            corrected_code = corrected_code.replace('```python', '').replace('```', '').strip()
        elif corrected_code.startswith('```'):
            corrected_code = corrected_code.replace('```', '').strip()
        
        # Apply additional library-specific fixes to the AI response
        corrected_code = apply_library_specific_fixes(corrected_code, library_name)
        
        safe_print(f" Debug: AI provided corrected code ({len(corrected_code)} chars)")
        return corrected_code, True
        
    except Exception as e:
        safe_print(f" Debug: AI correction failed: {str(e)}")
        return original_code, False

def generate_replacement_question(subject, topic, difficulty_level, bloom_level, requires_diagram, library_name=None):
    """
    Generate a completely new question to replace a failed one with enhanced library-specific templates
    
    Args:
        subject (str): Subject context
        topic (str): Topic context
        difficulty_level (str): Difficulty level
        bloom_level (int): Bloom taxonomy level
        requires_diagram (bool): Whether diagram is required
        library_name (str): Preferred library for diagram
    
    Returns:
        dict: New question data or None if failed
    """
    try:
        client = get_openai_client()
        
        # Use hybrid model selection for replacement question generation
        complexity_factors = {
            'subject': subject,
            'topic': topic,
            'requires_diagram': requires_diagram,
            'bloom_level_id': bloom_level,
            'replacement_generation': True
        }
        selected_model, model_reason = select_optimal_model('question_generation', complexity_factors)
        
        # Get library-specific working template if available
        working_template = ""
        if requires_diagram and library_name:
            working_template = get_library_working_templates(library_name)
        
        # Get library-specific error patterns for guidance
        error_patterns = {}
        if library_name:
            error_patterns = get_library_error_patterns(library_name)
        
        replacement_prompt = f"""
Generate a brand new {subject} question about {topic} for {difficulty_level} difficulty level.

**Requirements:**
- Subject: {subject}
- Topic: {topic}
- Difficulty: {difficulty_level}
- Bloom Level: {bloom_level}
- Diagram Required: {requires_diagram}
{f"- Preferred Library: {library_name}" if library_name else ""}

**Format Requirements:**
Question: [Your question here]
A. [Option A]
B. [Option B]  
C. [Option C]
D. [Option D]
Answer: [A/B/C/D]
Explanation: [Detailed explanation]
{"Library: " + library_name if requires_diagram and library_name else ""}
{f"PythonCode:\n```python\n[Simple, error-free {library_name} code using 'output.png' filename]\n```" if requires_diagram else ""}

**Library-Specific Guidelines:**
{f"- Library: {library_name}" if library_name else ""}
{f"- Working Template:\n```python\n{working_template}\n```" if working_template else ""}
{f"- Common Error Patterns to Avoid:\n" + "\n".join([f"  • {pattern}: {fix}" for pattern, fix in error_patterns.items()]) if error_patterns else ""}

**Important Rules:**
- Create a completely different question concept
- If diagram required, use the working template as a base
- Avoid common error patterns for this library
- Use standard library functions only
- Ensure code has no syntax errors
- Use 'output.png' as save filename
- Make the code robust and error-free
- Follow library-specific best practices
"""

        safe_print(f" Debug: Generating replacement question with {selected_model}...")
        
        response = client.chat.completions.create(
            model=selected_model,
            messages=[{"role": "user", "content": replacement_prompt}],
            temperature=0.7,
            max_tokens=2000
        )
        
        response_text = response.choices[0].message.content.strip()
        safe_print(f" Debug: Generated replacement question ({len(response_text)} chars)")
        
        # Parse the response (simplified parsing)
        lines = response_text.split('\n')
        question_data = {
            'question_text': '',
            'options': [],
            'correct_answer': '',
            'explanation': '',
            'library': library_name if requires_diagram else None,
            'diagram_code': None
        }
        
        for line in lines:
            if line.startswith('Question:'):
                question_data['question_text'] = line.replace('Question:', '').strip()
            elif line.startswith(('A.', 'B.', 'C.', 'D.')):
                question_data['options'].append(line[2:].strip())
            elif line.startswith('Answer:'):
                question_data['correct_answer'] = line.replace('Answer:', '').strip()
            elif line.startswith('Explanation:'):
                question_data['explanation'] = line.replace('Explanation:', '').strip()
            elif '```python' in line:
                # Extract code block
                code_start = response_text.find('```python') + 9
                code_end = response_text.find('```', code_start)
                if code_end > code_start:
                    question_data['diagram_code'] = response_text[code_start:code_end].strip()
        
        # Apply library-specific fixes to the generated code
        if question_data['diagram_code'] and library_name:
            question_data['diagram_code'] = apply_library_specific_fixes(question_data['diagram_code'], library_name)
        
        return question_data if question_data['question_text'] else None
        
    except Exception as e:
        safe_print(f" Debug: Replacement question generation failed: {str(e)}")
        return None

# Library-specific error patterns and correction functions
def get_library_error_patterns(library_name):
    """
    Get library-specific error patterns and their fixes
    
    Args:
        library_name (str): Name of the library
    
    Returns:
        dict: Error patterns and their fixes
    """
    patterns = {
        'schemdraw': {
            "invalid syntax": "Fix element call syntax and method calls",
            "has no attribute 'dff'": "Use DFlipFlop instead of dff",
            "has no attribute 'Box'": "Use Rect instead of Box",
            "has no attribute 'Dff'": "Use DFlipFlop instead of Dff",
            "has no attribute 'OPAMP'": "Use Opamp instead of OPAMP",
            "name 'schem' is not defined": "Fix import statement - use schemdraw not schem",
            "module 'schemdraw.elements' has no attribute": "Check element name case sensitivity",
            "cannot assign to literal": "Fix variable assignment syntax",
            "d.add(": "Replace d.add() with d +=",
            "e.dff(": "Replace e.dff() with e.DFlipFlop(",
            "schem.Drawing": "Replace with schemdraw.Drawing",
            "import SchemDraw": "Replace with import schemdraw",
            "labelloc not defined in Element": "Use .label(loc='top') instead of .labelloc()",
            "Element.label() missing 1 required positional argument": "Provide label text as first argument",
            "invalid decimal literal": "Fix malformed parentheses in element calls",
            "not defined in Element": "Check element method names and parameters"
        },
        'matplotlib': {
            "module 'numpy' has no attribute 'factorial'": "Use scipy.special.factorial instead",
            "Legend.__init__() got an unexpected keyword argument": "Remove invalid legend parameters",
            "'seaborn-darkgrid' is not a valid package style": "Use seaborn-v0_8-darkgrid instead",
            "invalid syntax": "Check for malformed function calls",
            "cannot assign to literal": "Fix variable assignment syntax"
        },
        'seaborn': {
            "Legend.__init__() got an unexpected keyword argument": "Remove invalid legend parameters",
            "'seaborn-darkgrid' is not a valid package style": "Use seaborn-v0_8-darkgrid instead",
            "invalid syntax": "Check for malformed function calls",
            "cannot assign to literal": "Fix variable assignment syntax"
        },
        'networkx': {
            "invalid syntax": "Check for malformed function calls",
            "cannot assign to literal": "Fix variable assignment syntax",
            "name 'buffer' is not defined": "Fix plt.savefig() calls"
        },
        'plotly': {
            "invalid syntax": "Check for malformed function calls",
            "cannot assign to literal": "Fix variable assignment syntax"
        },
        'graphviz': {
            "invalid syntax": "Check for malformed function calls",
            "cannot assign to literal": "Fix variable assignment syntax"
        },
        'pillow': {
            "invalid syntax": "Check for malformed function calls",
            "cannot assign to literal": "Fix variable assignment syntax"
        },
        'turtle': {
            "invalid syntax": "Check for malformed function calls",
            "cannot assign to literal": "Fix variable assignment syntax"
        }
    }
    
    return patterns.get(library_name, {})

def get_library_working_templates(library_name):
    """
    Get working code templates for each library
    
    Args:
        library_name (str): Name of the library
    
    Returns:
        str: Working code template
    """
    templates = {
        'schemdraw': '''import schemdraw
import schemdraw.elements as e
from schemdraw import Drawing

d = schemdraw.Drawing()
# Create a simple circuit diagram
d += e.DFlipFlop(label='DFF')
d += e.Dot()
d += e.Line()
d += e.Dot()
d += e.Ground()
d.save('output.png')''',
        
        'matplotlib': '''import matplotlib.pyplot as plt
import numpy as np

fig, ax = plt.subplots(figsize=(8, 6))
x = np.linspace(0, 10, 100)
y = np.sin(x)
ax.plot(x, y)
ax.set_title('Sample Plot')
ax.set_xlabel('X')
ax.set_ylabel('Y')
plt.savefig('output.png', dpi=300, bbox_inches='tight')
plt.close()''',
        
        'seaborn': '''import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np

# Set style
sns.set_style("whitegrid")

# Create data
data = np.random.randn(100)
fig, ax = plt.subplots(figsize=(8, 6))
sns.histplot(data, bins=20, ax=ax)
ax.set_title('Sample Histogram')
plt.savefig('output.png', dpi=300, bbox_inches='tight')
plt.close()''',
        
        'networkx': '''import networkx as nx
import matplotlib.pyplot as plt

G = nx.Graph()
G.add_edges_from([(1, 2), (2, 3), (3, 1)])
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color='lightblue', 
        node_size=500, font_size=16, font_weight='bold')
plt.savefig('output.png', dpi=300, bbox_inches='tight')
plt.close()''',
        
        'plotly': '''import plotly.graph_objects as go
import numpy as np

x = np.linspace(0, 10, 100)
y = np.sin(x)

fig = go.Figure(data=go.Scatter(x=x, y=y, mode='lines'))
fig.update_layout(title='Sample Plot', xaxis_title='X', yaxis_title='Y')
fig.write_image('output.png')''',
        
        'graphviz': '''from graphviz import Digraph

dot = Digraph(comment='Sample Graph')
dot.node('A', 'Node A')
dot.node('B', 'Node B')
dot.edge('A', 'B')
dot.render('output', format='png', cleanup=True)''',
        
        'pillow': '''from PIL import Image, ImageDraw

# Create a simple image
img = Image.new('RGB', (400, 300), color='white')
draw = ImageDraw.Draw(img)
draw.rectangle([50, 50, 350, 250], outline='black', width=2)
draw.text((200, 150), 'Sample', fill='black')
img.save('output.png')''',
        
        'turtle': '''import turtle
import io
from PIL import Image

# Create turtle drawing
t = turtle.Turtle()
t.speed(0)
t.penup()
t.goto(-50, 0)
t.pendown()
t.circle(50)
t.hideturtle()

# Capture the canvas
canvas = turtle.getcanvas()
canvas.postscript(file='temp.ps')
img = Image.open('temp.ps')
img.save('output.png')'''
    }
    
    return templates.get(library_name, '')

def get_library_specific_correction_prompt(library_name, original_code, error_message, subject, topic):
    """
    Generate library-specific correction prompts
    
    Args:
        library_name (str): Name of the library
        original_code (str): Original code that failed
        error_message (str): Error message
        subject (str): Subject context
        topic (str): Topic context
    
    Returns:
        str: Library-specific correction prompt
    """
    
    error_patterns = get_library_error_patterns(library_name)
    working_template = get_library_working_templates(library_name)
    
    if library_name == 'schemdraw':
        return f"""
You are a schemdraw expert specializing in electronic circuit diagrams. Fix this code that failed with error: {error_message}

**Context:**
- Subject: {subject}
- Topic: {topic}
- Library: schemdraw (electronic circuits)

**Original Code:**
```python
{original_code}
```

**Common Schemdraw Fixes:**
- Replace e.dff() with e.DFlipFlop()
- Replace e.Box() with e.Rect()
- Replace e.OPAMP() with e.Opamp()
- Replace d.add() with d +=
- Replace schem.Drawing() with schemdraw.Drawing()
- Remove invalid parameters: clk=, D=, Q=, reseta=, resetb=
- Fix import statements: use 'import schemdraw' not 'import SchemDraw'
- Use proper element names: DFlipFlop, Rect, Dot, Line, Arrow, Opamp
- Fix label syntax: use .label('text', loc='top') not .labelloc()
- Provide label text as first argument: .label('text') not .label()
- Fix malformed parentheses in element calls
- Use simple element calls: e.Dot(), e.Line(), e.Ground()

**Working Template:**
```python
{working_template}
```

**Your Task:**
1. Fix the specific error: {error_message}
2. Apply schemdraw-specific corrections
3. Ensure code uses 'output.png' as filename
4. Make the code robust and error-free
5. Use simple, proven element combinations

**Output Format:**
Provide ONLY the corrected Python code without any explanations or markdown.
"""

    elif library_name == 'matplotlib':
        return f"""
You are a matplotlib expert specializing in data visualization. Fix this code that failed with error: {error_message}

**Context:**
- Subject: {subject}
- Topic: {topic}
- Library: matplotlib (data visualization)

**Original Code:**
```python
{original_code}
```

**Common Matplotlib Fixes:**
- Replace np.factorial with scipy.special.factorial
- Remove invalid legend parameters: locolor, color, facecolor, edgecolor
- Update deprecated styles: seaborn-darkgrid → seaborn-v0_8-darkgrid
- Fix plt.savefig() calls to use 'output.png'
- Ensure proper import statements

**Working Template:**
```python
{working_template}
```

**Your Task:**
1. Fix the specific error: {error_message}
2. Apply matplotlib-specific corrections
3. Ensure code uses 'output.png' as filename
4. Make the code robust and error-free

**Output Format:**
Provide ONLY the corrected Python code without any explanations or markdown.
"""

    elif library_name == 'seaborn':
        return f"""
You are a seaborn expert specializing in statistical visualization. Fix this code that failed with error: {error_message}

**Context:**
- Subject: {subject}
- Topic: {topic}
- Library: seaborn (statistical plots)

**Original Code:**
```python
{original_code}
```

**Common Seaborn Fixes:**
- Remove invalid legend parameters: locolor, color, facecolor, edgecolor
- Update deprecated styles: seaborn-darkgrid → seaborn-v0_8-darkgrid
- Fix plt.savefig() calls to use 'output.png'
- Ensure proper import statements
- Use sns.set_style() instead of deprecated styles

**Working Template:**
```python
{working_template}
```

**Your Task:**
1. Fix the specific error: {error_message}
2. Apply seaborn-specific corrections
3. Ensure code uses 'output.png' as filename
4. Make the code robust and error-free

**Output Format:**
Provide ONLY the corrected Python code without any explanations or markdown.
"""

    else:
        # Generic correction prompt for other libraries
        return f"""
You are a Python expert specializing in {library_name}. Fix this code that failed with error: {error_message}

**Context:**
- Subject: {subject}
- Topic: {topic}
- Library: {library_name}

**Original Code:**
```python
{original_code}
```

**Working Template:**
```python
{working_template}
```

**Your Task:**
1. Fix the specific error: {error_message}
2. Apply {library_name}-specific corrections
3. Ensure code uses 'output.png' as filename
4. Make the code robust and error-free

**Output Format:**
Provide ONLY the corrected Python code without any explanations or markdown.
"""

def apply_library_specific_fixes(code, library_name):
    """
    Apply library-specific code fixes using regex patterns
    
    Args:
        code (str): Original code
        library_name (str): Name of the library
    
    Returns:
        str: Fixed code
    """
    if library_name == 'schemdraw':
        # Schemdraw-specific fixes
        fixes = [
            # Basic element name fixes
            (r'e\.dff\(', 'e.DFlipFlop('),
            (r'e\.Box\(', 'e.Rect('),
            (r'e\.OPAMP\(', 'e.Opamp('),
            (r'e\.ARROW\(', 'e.Arrow('),
            (r'e\.DOT\(', 'e.Dot('),
            (r'e\.LINE\(', 'e.Line('),
            
            # Method call fixes
            (r'd\.add\(', 'd +='),
            (r'schem\.Drawing', 'schemdraw.Drawing'),
            (r'import SchemDraw', 'import schemdraw'),
            (r'import SchemDraw as schem', 'import schemdraw'),
            
            # Parameter fixes
            (r'clk=', ''),
            (r'D=', ''),
            (r'Q=', ''),
            (r'reseta=', ''),
            (r'resetb=', ''),
            
            # Label method fixes
            (r'\.labelloc\(', '.label(loc='),
            (r'\.labelcolor\(', '.label(color='),
            (r'\.label\(([^)]+)\)\.label\(', r'.label(\1, '),
            (r'\.label\(([^)]+)\)\.labelloc\(', r'.label(\1, loc='),
            (r'\.label\(([^)]+)\)\.labelcolor\(', r'.label(\1, color='),
            
            # Invalid method removals
            (r'\.left\(\)\.left\(\)', '.left()'),
            (r'\.right\(\)\.right\(\)', '.right()'),
            (r'\.up\(\)\.up\(\)', '.up()'),
            (r'\.down\(\)\.down\(\)', '.down()'),
            
            # Fix malformed parentheses
            (r'\(\.label\(', '(.label('),
            (r'\(\.left\(', '(.left('),
            (r'\(\.right\(', '(.right('),
            (r'\(\.up\(', '(.up('),
            (r'\(\.down\(', '(.down('),
            
            # Fix decimal literal errors
            (r'w=4\.label\(', 'w=4).label('),
            (r'h=4\.label\(', 'h=4).label('),
            
            # Fix invalid element attributes
            (r'\.label\(([^)]+), loc=([^)]+)\)', r'.label(\1, loc=\2)'),
            (r'\.label\(([^)]+), color=([^)]+)\)', r'.label(\1, color=\2)'),
            
            # Remove invalid parameters
            (r', loc=([^)]+)', ''),
            (r', color=([^)]+)', ''),
            
            # Fix basic syntax errors
            (r'\.label\(\)', '.label("")'),
            (r'\.label\(([^)]*)\)\.label\(', r'.label(\1, '),
        ]
        
        for pattern, replacement in fixes:
            code = re.sub(pattern, replacement, code)
    
    elif library_name == 'matplotlib':
        # Matplotlib-specific fixes
        fixes = [
            (r'np\.factorial', 'scipy.special.factorial'),
            (r'seaborn-darkgrid', 'seaborn-v0_8-darkgrid'),
            (r'seaborn-whitegrid', 'seaborn-v0_8-whitegrid'),
            (r'seaborn-dark', 'seaborn-v0_8-dark'),
            (r'seaborn-white', 'seaborn-v0_8-white'),
            (r'seaborn-ticks', 'seaborn-v0_8-ticks'),
            (r'locolor=', ''),
            (r'color=', ''),
            (r'facecolor=', ''),
            (r'edgecolor=', ''),
        ]
        
        for pattern, replacement in fixes:
            code = re.sub(pattern, replacement, code)
    
    elif library_name == 'seaborn':
        # Seaborn-specific fixes (similar to matplotlib)
        fixes = [
            (r'seaborn-darkgrid', 'seaborn-v0_8-darkgrid'),
            (r'seaborn-whitegrid', 'seaborn-v0_8-whitegrid'),
            (r'seaborn-dark', 'seaborn-v0_8-dark'),
            (r'seaborn-white', 'seaborn-v0_8-white'),
            (r'seaborn-ticks', 'seaborn-v0_8-ticks'),
            (r'locolor=', ''),
            (r'color=', ''),
            (r'facecolor=', ''),
            (r'edgecolor=', ''),
        ]
        
        for pattern, replacement in fixes:
            code = re.sub(pattern, replacement, code)
    
    return code