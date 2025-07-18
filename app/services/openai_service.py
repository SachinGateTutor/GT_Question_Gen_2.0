import os
import openai
import traceback
import re

def get_openai_client():
    # Hardcoded API key for limited use
    api_key = "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"
    print(f"Debug: Using hardcoded API key: {api_key[:20]}...")
    print("Debug: Creating OpenAI client with valid API key")
    return openai.OpenAI(api_key=api_key)

def determine_best_library(subject, topic, requires_diagram):
    """Stage 1: Determine the best library for the given subject/topic"""
    if not requires_diagram:
        return None, None
    
    client = get_openai_client()
    
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
            model="gpt-3.5-turbo",
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
            elif line and line.startswith('Reason:'):
                parts = line.split(':', 1)
                if len(parts) > 1:
                    reason = parts[1].strip()
        
        print(f"🎯 Selected library: {library_name} - {reason}")
        return library_name, reason
        
    except Exception as e:
        print(f"Error determining library: {e}")
        return "schemdraw", "Fallback to schemdraw"

def generate_mcq_and_diagram(data):
    try:
        print("🔍 Debug: Starting generate_mcq_and_diagram")
        print(f"🔍 Debug: Input data: {data}")
        
        stream = data.get('stream', 'CS')
        subject = data.get('subject', 'Data Structures')
        topic = data.get('topic', 'Binary Trees')
        question_type = data.get('question_type', 'MCQ')
        requires_diagram = data.get('requires_diagram', False)
        requires_option_diagrams = data.get('requires_option_diagrams', False)
        custom_prompt = data.get('custom_prompt', '')

        print(f"🔍 Debug: Parsed values - stream: {stream}, subject: {subject}, topic: {topic}")
        print(f"🔍 Debug: question_type: {question_type}, requires_diagram: {requires_diagram}, requires_option_diagrams: {requires_option_diagrams}")

        # Enhanced programming topics for maximum diversity
        programming_topics = [
            # Programming Languages
            'Java Programming', 'C++ Programming', 'Python Programming', 'JavaScript Programming',
            'C# Programming', 'C Programming', 'Ruby Programming', 'Go Programming',
            
            # Web Development
            'Web Development', 'Frontend Development', 'Backend Development', 'Full Stack Development',
            'HTML/CSS', 'React Development', 'Angular Development', 'Node.js Development',
            
            # Database and Data
            'Database Programming', 'SQL Programming', 'NoSQL Programming', 'Data Analysis',
            'Big Data Processing', 'Data Mining', 'Machine Learning Programming',
            
            # Software Engineering
            'Object-Oriented Programming', 'Functional Programming', 'Design Patterns',
            'Software Architecture', 'System Design', 'API Development', 'Microservices',
            
            # Algorithms and Data Structures
            'Data Structures with Programs', 'Algorithms Implementation', 'Algorithm Design',
            'Competitive Programming', 'Dynamic Programming', 'Graph Algorithms',
            
            # Specialized Programming
            'Game Development', 'Mobile App Development', 'Embedded Systems Programming',
            'System Programming', 'Network Programming', 'Security Programming',
            
            # Modern Development
            'DevOps Programming', 'Cloud Computing', 'Containerization', 'CI/CD Programming',
            'Test-Driven Development', 'Agile Programming', 'Clean Code Programming'
        ]
        
        is_programming_topic = any(prog_topic.lower() in topic.lower() for prog_topic in programming_topics)

        # Get OpenAI client
        client = get_openai_client()
        if not client:
            print("❌ Debug: OpenAI client creation failed")
            return {
                'error': 'OpenAI API key not set. Please add your API key to the .env file.',
                'question_text': 'Sample question for testing',
                'options': ['A', 'B', 'C', 'D'],
                'correct_answer': 'A',
                'explanation': 'Sample explanation for testing.',
                'diagram_code': None,
                'library_used': None,
                'option_diagram_codes': None
            }
        
        print("✅ Debug: OpenAI client created successfully")

        # Stage 1: Determine best library
        library_name, library_reason = determine_best_library(subject, topic, requires_diagram or requires_option_diagrams)
        
        # Stage 2: Generate question and diagram code
        if is_programming_topic:
            # Generate programming question with code snippet
            prompt = generate_programming_question_prompt(topic, question_type, custom_prompt)
        elif (requires_diagram or requires_option_diagrams) and library_name:
            # Generate diagram-based question
            prompt = generate_diagram_question_prompt(topic, subject, stream, question_type, requires_option_diagrams, library_name, custom_prompt)
        else:
            # Generate regular question
            prompt = generate_regular_question_prompt(topic, subject, stream, question_type, custom_prompt)

        print("🔄 Debug: Sending request to OpenAI...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content
        print("✅ Debug: Got response from OpenAI")
        print("=== RAW OPENAI RESPONSE ===")
        print(content)
        print("===========================")

        # Parse response
        question_text = None
        options = []
        correct_answer = None
        explanation = None
        diagram_code = None
        option_diagram_codes = {'A': '', 'B': '', 'C': '', 'D': ''}
        detected_library = library_name

        lines = content.split('\n') if content else []
        code_lines = []
        option_code_lines = {'A': [], 'B': [], 'C': [], 'D': []}
        in_code = False
        in_option_code = False
        current_option = None
        collecting_explanation = False
        
        # For programming questions, extract code snippet from question text
        code_snippet = None
        if is_programming_topic and content:
            # Look for code blocks in the entire response
            import re
            code_pattern = r'```(\w+)\n(.*?)```'
            code_matches = re.findall(code_pattern, content, re.DOTALL)
            if code_matches:
                # Take the first code block found
                language, code_content = code_matches[0]
                code_snippet = f"```{language}\n{code_content}\n```"
                print(f"🔍 Debug: Extracted code snippet for programming question")
        
        for line in lines:
            if line is None:
                continue
            line = line.strip()
            if not line:
                continue
            
            # Only call split if line contains ':' or '.' as needed
            if line.lower().startswith('question:') and ':' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    question_text = parts[1].strip()
                collecting_explanation = False
            elif line.startswith('A.') and '.' in line:
                parts = line.split('.', 1)
                if len(parts) > 1:
                    options.append(parts[1].strip())
                collecting_explanation = False
            elif line.startswith('B.') and '.' in line:
                parts = line.split('.', 1)
                if len(parts) > 1:
                    options.append(parts[1].strip())
                collecting_explanation = False
            elif line.startswith('C.') and '.' in line:
                parts = line.split('.', 1)
                if len(parts) > 1:
                    options.append(parts[1].strip())
                collecting_explanation = False
            elif line.startswith('D.') and '.' in line:
                parts = line.split('.', 1)
                if len(parts) > 1:
                    options.append(parts[1].strip())
                collecting_explanation = False
            # Handle "Option A:" format as well
            elif line.lower().startswith('option a:') and ':' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    options.append(parts[1].strip())
                collecting_explanation = False
            elif line.lower().startswith('option b:') and ':' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    options.append(parts[1].strip())
                collecting_explanation = False
            elif line.lower().startswith('option c:') and ':' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    options.append(parts[1].strip())
                collecting_explanation = False
            elif line.lower().startswith('option d:') and ':' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    options.append(parts[1].strip())
                collecting_explanation = False
            elif line.lower().startswith('answer:') and ':' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    correct_answer = parts[1].strip()
                collecting_explanation = False
            elif line.lower().startswith('explanation:') and ':' in line:
                parts = line.split(':', 1)
                explanation = parts[1].strip() if len(parts) > 1 else ''
                collecting_explanation = True
            elif line.lower().startswith(('library:', 'pythoncode:')):
                collecting_explanation = False
            # --- Option Diagram Code Extraction ---
            elif any(line.lower().startswith(f'option{opt.lower()}code:') for opt in ['A', 'B', 'C', 'D']):
                # Start of an option code block (OptionACode: format)
                in_option_code = True
                in_code = False
                for opt in ['A', 'B', 'C', 'D']:
                    if line.lower().startswith(f'option{opt.lower()}code:'):
                        current_option = opt
                        break
                continue
            elif any(line.lower().startswith(f'option {opt.lower()}:') for opt in ['A', 'B', 'C', 'D']):
                # Start of an option code block (Option A: format)
                in_option_code = True
                in_code = False
                for opt in ['A', 'B', 'C', 'D']:
                    if line.lower().startswith(f'option {opt.lower()}:'):
                        current_option = opt
                        break
                continue
            elif in_option_code and '```python' in line:
                in_code = True
                continue
            elif in_option_code and '```' in line and in_code:
                in_code = False
                in_option_code = False
                current_option = None
                continue
            elif in_option_code and in_code and current_option:
                option_code_lines[current_option].append(line)
            # --- End Option Diagram Code Extraction ---
            elif requires_diagram and '```python' in line:
                in_code = True
                collecting_explanation = False
            elif requires_diagram and '```' in line and in_code:
                in_code = False
            elif requires_diagram and in_code:
                code_lines.append(line)
            elif collecting_explanation:
                # Stop collecting if we hit another field
                if line.lower().startswith(('library:', 'pythoncode:', 'answer:', 'question:', 'a.', 'b.', 'c.', 'd.')):
                    collecting_explanation = False
                else:
                    if explanation:
                        explanation += '\n' + line
                    else:
                        explanation = line
        if code_lines and requires_diagram:
            diagram_code = '\n'.join(code_lines)

        # Process option diagram codes
        if requires_option_diagrams:
            for option, lines in option_code_lines.items():
                if lines:
                    option_diagram_codes[option] = '\n'.join(lines)

        # Fallback: If no options were parsed but we have option diagrams, create default options
        if not options and any(option_diagram_codes.values()):
            options = ['Option A', 'Option B', 'Option C', 'Option D']
            print("⚠️ Debug: No options parsed, using default option labels")
        
        # Fallback: If no options were parsed, try to extract from the response
        if not options and content:
            print("⚠️ Debug: No options parsed, attempting to extract from response...")
            import re
            # Look for patterns like "Option A:", "A.", etc.
            option_patterns = [
                r'Option A:\s*(.+)',
                r'Option B:\s*(.+)',
                r'Option C:\s*(.+)',
                r'Option D:\s*(.+)',
                r'A\.\s*(.+)',
                r'B\.\s*(.+)',
                r'C\.\s*(.+)',
                r'D\.\s*(.+)'
            ]
            
            for pattern in option_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    options.extend(matches)
                    print(f"🔍 Debug: Found options using pattern: {pattern}")
                    break
            
            # If still no options, use default data structures
            if not options:
                options = ['Linked List', 'Binary Tree', 'Hash Table', 'Stack']
                print("⚠️ Debug: Using default options")
        
        # Fallback: If no diagram code, create a simple one
        if not diagram_code and requires_diagram:
            print("⚠️ Debug: No diagram code found, creating fallback diagram")
            if library_name == 'graphviz':
                diagram_code = '''import graphviz
dot = graphviz.Digraph()
dot.node('A', 'Start', shape='ellipse', fillcolor='lightgreen', style='filled')
dot.node('B', 'Process', shape='box', fillcolor='lightblue', style='filled')
dot.node('C', 'Decision', shape='diamond', fillcolor='lightyellow', style='filled')
dot.node('D', 'End', shape='octagon', fillcolor='lightcoral', style='filled')
dot.edge('A', 'B', label='to process', color='red', style='dashed')
dot.edge('B', 'C', label='check', color='blue', style='solid')
dot.edge('C', 'D', label='complete', color='green', style='bold')
dot.render('temp', format='png', cleanup=True)'''
            elif library_name == 'networkx':
                diagram_code = '''import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO
G = nx.Graph()
G.add_node(1, color='red', size=1000, label='Start')
G.add_node(2, color='blue', size=800, label='Process')
G.add_node(3, color='green', size=1200, label='End')
G.add_edge(1, 2, color='red', width=3)
G.add_edge(2, 3, color='blue', width=2)
nx.draw(G, with_labels=True, font_weight='bold', node_color='lightblue', node_size=1000, edge_color='red', width=2)
plt.savefig(buffer, format='png', bbox_inches='tight')
plt.close()'''
            else:
                diagram_code = '''import matplotlib.pyplot as plt
import numpy as np
from io import BytesIO
fig, ax = plt.subplots(figsize=(10, 8))
x = np.linspace(0, 10, 100)
y = np.sin(x)
ax.plot(x, y, color='red', linewidth=2, marker='o')
ax.set_title('Sample Diagram', fontsize=14, fontweight='bold')
plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
plt.close()'''

        # Debug prints for parsed values
        print("Parsed question_text:", question_text)
        print("Parsed options:", options)
        print("Parsed correct_answer:", correct_answer)
        print("Parsed explanation:", explanation)
        print("Parsed option_diagram_codes:", option_diagram_codes)

        # For programming questions, append code snippet to question text
        if is_programming_topic and code_snippet:
            if question_text:
                question_text += f"\n\n{code_snippet}"
            else:
                question_text = code_snippet

        return {
            'question_text': question_text,
            'options': options,
            'correct_answer': correct_answer,
            'explanation': explanation,
            'diagram_code': diagram_code,
            'library_used': detected_library,
            'option_diagram_codes': option_diagram_codes
        }
    except Exception as e:
        print(f"❌ Error in OpenAI service: {e}")
        print("🔍 Debug: Full exception details:")
        traceback.print_exc()
        return {
            'error': f'OpenAI API error: {str(e)}',
            'question_text': 'Sample question for testing',
            'options': ['A', 'B', 'C', 'D'],
            'correct_answer': 'A',
            'explanation': 'This is a sample response for testing.',
            'diagram_code': None,
            'library_used': 'schemdraw',
            'option_diagram_codes': {'A': None, 'B': None, 'C': None, 'D': None}
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
from io import BytesIO

# Create RICH, COLORFUL matplotlib visualization
plt.style.use('default')  # Use modern styling
fig, ax = plt.subplots(figsize=(10, 8))
# Add diverse plot elements with colors, markers, and annotations
# Create an informative and visually appealing plot
# IMPORTANT: Use proper color names and ensure colors are applied correctly
# Example: ax.plot(x, y, color='red', linewidth=2, marker='o')
# Example: ax.scatter(x, y, c=colors, s=sizes, alpha=0.6)
# Example: ax.bar(categories, values, color=colors, alpha=0.7)
# Example: ax.fill_between(x, y1, y2, color='lightblue', alpha=0.3)
plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
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
from io import BytesIO

# Create RICH, HIERARCHICAL graphviz diagram with diverse elements
dot = graphviz.Digraph()
# Add diverse nodes and edges with different shapes, colors, and styles
# Create an illustrative diagram showing clear flow and relationships
# Example: dot.node('A', 'Start', shape='ellipse', fillcolor='lightgreen', style='filled')
# Example: dot.edge('A', 'B', label='to decision', color='red', style='dashed')
# CRITICAL: Use dot.edge() for individual edges, NOT dot.edges() with style/color parameters
# CRITICAL: dot.edges() only accepts tuples like [('A', 'B'), ('B', 'C')] - no styling
# Note: dot.render() saves to file, not buffer
dot.render('temp', format='png', cleanup=True)
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
2. Always end with: plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
3. Always close with: plt.close()
4. Make plots informative and visually appealing
5. IMPORTANT: Use proper color names and ensure colors are applied correctly""",
        
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
4. Use dot.render('temp', format='png', cleanup=True)
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

def generate_programming_question_prompt(topic, question_type, custom_prompt):
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

The question MUST include a code snippet in {language} and ask about its output, behavior, or analysis.

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

def generate_diagram_question_prompt(topic, subject, stream, question_type, requires_option_diagrams, library_name, custom_prompt):
    """Generate a prompt for diagram-based questions with enhanced visual diversity"""
    
    import random
    import time
    
    # Create a seed based on current time to ensure different questions
    random.seed(time.time())
    timestamp_variation = int(time.time() * 1000) % 1000
    
    option_diagram_instructions = ""
    if requires_option_diagrams:
        option_diagram_instructions = f"""

IMPORTANT: You must generate 4 separate RICH, DIVERSE diagrams for options A, B, C, and D.
Each option should have its own unique, illustrative diagram that clearly represents the concept described in that option.

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
from io import BytesIO
# Create RICH, HIERARCHICAL graphviz diagram for Option A
dot = graphviz.Digraph()
dot.node('A', 'Root', shape='circle', style='filled', fillcolor="lightblue")
dot.node('B', 'Left Child', shape='box', style='filled', fillcolor="lightgreen")
dot.node('C', 'Right Child', shape='box', style='filled', fillcolor="lightgreen")
dot.edge('A', 'B', label='Root->Left', color="blue", style='dashed')
dot.edge('A', 'C', label='Root->Right', color="blue", style='dashed')
dot.render('temp', format='png', cleanup=True)
```

OptionBCode:
```python
# Generate RICH, DIVERSE diagram for Option B with different colors, shapes, and layout
import graphviz
from io import BytesIO
# Create RICH, HIERARCHICAL graphviz diagram for Option B
dot = graphviz.Digraph()
dot.node('A', 'Start', shape='ellipse', style='filled', fillcolor="lightgreen")
dot.node('B', 'Process', shape='box', style='filled', fillcolor="lightyellow")
dot.node('C', 'Decision', shape='diamond', style='filled', fillcolor="lightcoral")
dot.edge('A', 'B', label='to process', color="red", style='dashed')
dot.edge('B', 'C', label='to decision', color="blue", style='solid')
dot.render('temp', format='png', cleanup=True)
```

OptionCCode:
```python
# Generate RICH, DIVERSE diagram for Option C with unique visual style and elements
import graphviz
from io import BytesIO
# Create RICH, HIERARCHICAL graphviz diagram for Option C
dot = graphviz.Digraph()
dot.node('A', 'Input', shape='parallelogram', style='filled', fillcolor="lightcyan")
dot.node('B', 'Process', shape='box', style='filled', fillcolor="lightpink")
dot.node('C', 'Output', shape='ellipse', style='filled', fillcolor="lightyellow")
dot.edge('A', 'B', label='process', color="green", style='bold')
dot.edge('B', 'C', label='result', color="purple", style='dotted')
dot.render('temp', format='png', cleanup=True)
```

OptionDCode:
```python
# Generate RICH, DIVERSE diagram for Option D with distinct colors, shapes, and annotations
import graphviz
from io import BytesIO
# Create RICH, HIERARCHICAL graphviz diagram for Option D
dot = graphviz.Digraph()
dot.node('A', 'Data', shape='hexagon', style='filled', fillcolor="lightgray")
dot.node('B', 'Analysis', shape='box', style='filled', fillcolor="lightblue")
dot.node('C', 'Result', shape='circle', style='filled', fillcolor="lightgreen")
dot.edge('A', 'B', label='analyze', color="orange", style='dashed')
dot.edge('B', 'C', label='output', color="brown", style='solid')
dot.render('temp', format='png', cleanup=True)
```

CRITICAL: Each option diagram should be visually distinct, rich in detail, and clearly represent the concept described in that option.

IMPORTANT: Generate ACTUAL WORKING Python code for each option diagram. Do NOT use placeholder text like "{get_library_specific_prompt(library_name)}" - replace it with real, executable diagram code.

Each OptionACode, OptionBCode, OptionCCode, and OptionDCode must contain complete, working Python code that creates a unique diagram.
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
- Add at least 4 nodes with different shapes: 'box', 'circle', 'ellipse', 'diamond', 'triangle', 'hexagon', 'octagon'
- Add at least 4 edges with different styles: 'solid', 'dashed', 'dotted', 'bold'
- Use different colors for nodes and edges
- Add labels to nodes and edges
- Use: dot.render('diagram', format='png', cleanup=True)
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
    
    prompt = f"""
Generate a {question_type} question for the topic '{topic}' in the subject '{subject}' ({stream} stream).

The question MUST include a relevant RICH, ILLUSTRATIVE diagram using the {library_name} library.
{option_diagram_instructions}

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
- Use $\frac{{a}}{{b}}$ for fractions
- Use $\sqrt{{x}}$ for square roots
- Use $\pi$, $\theta$, $\alpha$, etc. for Greek letters
- Use $\leq$, $\geq$, $\neq$ for comparison operators
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

def generate_regular_question_prompt(topic, subject, stream, question_type, custom_prompt):
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

IMPORTANT REQUIREMENTS FOR QUESTION DIVERSITY:
1. Use this specific question format: "{selected_question_type}"
2. {variation_instruction}
3. Make the question challenging but fair
4. Include realistic distractors in options
5. Cover different aspects of the topic (conceptual, practical, analytical)
6. Use real-world examples when appropriate
7. Include mathematical concepts where relevant

IMPORTANT: For mathematical equations, use proper LaTeX notation:
- Use $f(x) = x^2$ for inline equations
- Use $\frac{{a}}{{b}}$ for fractions
- Use $\sqrt{{x}}$ for square roots
- Use $\pi$, $\theta$, $\alpha$, etc. for Greek letters
- Use $\leq$, $\geq$, $\neq$ for comparison operators
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

def parse_openai_response(response_text):
    """Parse the OpenAI response to extract question components"""
    print("🔍 Debug: Parsing OpenAI response...")
    print(f"🔍 Debug: Response length: {len(response_text)}")
    
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
        print(f"🔍 Debug: Looking for code snippets in response...")
        print(f"🔍 Debug: Response lines: {len(lines)}")

        # 1. Look for 'Code:' section and extract the next code block
        code_section_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith('Code:'):
                code_section_start = i
                print(f"🔍 Debug: Found 'Code:' section at line {i}")
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
                print(f"🔍 Debug: Found code snippet in Code section ({language}): {code_snippet[:100]}...")
        
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
                print(f"🔍 Debug: Found fallback code snippet ({language}): {code_snippet[:100]}...")
        
        if not code_snippet:
            print("⚠️ Debug: No code snippet found in response")
            print("🔍 Debug: First 10 lines of response:")
            for i, line in enumerate(lines[:10]):
                print(f"  {i}: {line.strip()}")
        
        # Always append code snippet to question text if found (for programming questions)
        if code_snippet:
            print(f"🔍 Debug: Appending code snippet to question text")
            question_text = f"{question_text}\n\n```{language}\n{code_snippet}\n```"
        
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
            print(f"⚠️ Debug: Only {len(options)} options found, adding default options")
            while len(options) < 4:
                options.append(f"Option {chr(65 + len(options))}")
        elif len(options) > 4:
            print(f"⚠️ Debug: {len(options)} options found, keeping only first 4")
            options = options[:4]
        
        # Extract correct answer
        for line in lines:
            line = line.strip()
            if line.startswith('Answer:'):
                correct_answer = line.replace('Answer:', '').strip()
                break
        
        # Extract explanation
        explanation_start = None
        for i, line in enumerate(lines):
            if line.strip().startswith('Explanation:'):
                explanation_start = i
                break
        
        if explanation_start is not None:
            explanation_lines = []
            for line in lines[explanation_start + 1:]:
                if line.strip().startswith(('Question:', 'A.', 'B.', 'C.', 'D.', 'Answer:', 'Library:', 'PythonCode:', 'OptionACode:', 'OptionBCode:', 'OptionCCode:', 'OptionDCode:')):
                    break
                explanation_lines.append(line)
            explanation = '\n'.join(explanation_lines).strip()
        
        # Extract library used
        for line in lines:
            line = line.strip()
            if line.startswith('Library:'):
                library_used = line.replace('Library:', '').strip()
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
        
        # Extract option diagram codes - only if they are properly formatted and not mixed with main diagram
        option_codes = ['OptionACode:', 'OptionBCode:', 'OptionCCode:', 'OptionDCode:']
        option_labels = ['A', 'B', 'C', 'D']
        
        # First check if we're in a section that should have option diagrams
        has_option_section = any(option_code in response_text for option_code in option_codes)
        
        if has_option_section:
        for option_code, option_label in zip(option_codes, option_labels):
            code_start = None
            code_end = None
            for i, line in enumerate(lines):
                if option_code in line:
                    code_start = i
                elif code_start is not None and '```' in line:
                    if code_end is None:
                        code_end = i
                        break
            
            if code_start is not None and code_end is not None:
                option_code_lines = lines[code_start + 1:code_end]
                    option_code_text = '\n'.join(option_code_lines)
                    
                    # Validate that the code is not just placeholder text
                    if option_code_text and not option_code_text.strip().startswith('#'):
                        # Check if it contains actual code (not just comments)
                        if any(keyword in option_code_text for keyword in ['import ', 'def ', 'class ', '= ', '+', '-', '*', '/']):
                            option_diagram_codes[option_label] = option_code_text
                        else:
                            print(f"⚠️ Debug: Option {option_label} code appears to be placeholder text")
                            option_diagram_codes[option_label] = None
                    else:
                        print(f"⚠️ Debug: Option {option_label} code is empty or just comments")
                        option_diagram_codes[option_label] = None
        else:
            print("🔍 Debug: No option diagram section found, skipping option diagram parsing")
        
        # If no options were parsed, use default labels
        if not options:
            print("⚠️ Debug: No options parsed, using default option labels")
            options = ['Option A', 'Option B', 'Option C', 'Option D']
        
        # If no correct answer found, default to A
        if not correct_answer:
            print("⚠️ Debug: No correct answer found, defaulting to A")
            correct_answer = 'A'
        
        # If no library specified, default to schemdraw
        if not library_used:
            library_used = 'schemdraw'
        
        print(f"🔍 Debug: Parsed question_text: {question_text}")
        print(f"🔍 Debug: Parsed options: {options}")
        print(f"🔍 Debug: Parsed correct_answer: {correct_answer}")
        print(f"🔍 Debug: Parsed explanation: {explanation[:100]}...")
        print(f"🔍 Debug: Parsed option_diagram_codes: {option_diagram_codes}")
        
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
        print(f"❌ Debug: Error parsing response: {str(e)}")
        return {
            'question_text': 'Error parsing question',
            'options': ['Option A', 'Option B', 'Option C', 'Option D'],
            'correct_answer': 'A',
            'explanation': 'Error parsing explanation',
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