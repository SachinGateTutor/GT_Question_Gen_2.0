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
1. **schemdraw** - Electronic circuits, logic gates, simple block diagrams
2. **matplotlib** - Mathematical plots, charts, graphs, 2D visualizations
3. **networkx** - Network graphs, social networks, relationship diagrams
4. **graphviz** - Flowcharts, process diagrams, hierarchical structures
5. **plotly** - Interactive charts, 3D plots, statistical visualizations
6. **seaborn** - Statistical plots, data visualizations
7. **pillow** - Image manipulation, simple geometric shapes
8. **turtle** - Simple geometric drawings, educational diagrams

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
        
        for line in content.split('\n'):
            if line.startswith('Library:'):
                library_name = line.split(':', 1)[1].strip()
            elif line.startswith('Reason:'):
                reason = line.split(':', 1)[1].strip()
        
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
        custom_prompt = data.get('custom_prompt', '')

        print(f"🔍 Debug: Parsed values - stream: {stream}, subject: {subject}, topic: {topic}")
        print(f"🔍 Debug: question_type: {question_type}, requires_diagram: {requires_diagram}")

        # Get OpenAI client
        client = get_openai_client()
        if not client:
            print("❌ Debug: OpenAI client creation failed")
            return {
                'error': 'OpenAI API key not set. Please add your API key to the .env file.',
                'question_text': 'Sample question for testing',
                'options': ['A', 'B', 'C', 'D'],
                'correct_answer': 'A',
                'explanation': 'This is a sample response for testing.',
                'diagram_code': None,
                'library_used': None
            }
        
        print("✅ Debug: OpenAI client created successfully")

        # Stage 1: Determine best library
        library_name, library_reason = determine_best_library(subject, topic, requires_diagram)
        
        # Stage 2: Generate question and diagram code
        if requires_diagram and library_name:
            prompt = f"""
Generate a {question_type} question for the topic '{topic}' in the subject '{subject}' ({stream} stream).

The question MUST include a relevant diagram using the {library_name} library.

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
Explanation: <brief explanation with proper LaTeX notation>
Library: {library_name}
PythonCode:
```python
# Generate diagram using {library_name}
{get_library_specific_prompt(library_name)}
```

CRITICAL RULES for the PythonCode:
{get_library_rules(library_name)}
"""
        else:
            # Original prompt for no diagram or fallback
            prompt = f"""
Generate a {question_type} question for the topic '{topic}' in the subject '{subject}' ({stream} stream).

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
Explanation: <brief explanation with proper LaTeX notation>
PythonCode:
```python
import schemdraw
import schemdraw.elements as e
import schemdraw.flow as flow
import schemdraw.logic as logic
from schemdraw import Drawing

# Create a simple valid schemdraw diagram
d = Drawing()
# Add elements using proper schemdraw syntax
# Example: d += e.Resistor2()
# Example: d += logic.And()
# Example: d += flow.Start()
# Always end with: d.save(buffer)
```
CRITICAL RULES for the PythonCode:
1. Use ONLY valid schemdraw elements: e.Resistor2(), e.Capacitor2(), e.Inductor2(), logic.And(), logic.Or(), logic.Not(), flow.Start(), flow.Process(), flow.Decision(), flow.End()
2. NEVER use: e.AND2, e.OR2, e.LINE, or any non-existent elements
3. Use proper syntax: d += element_name()
4. Always end with: d.save(buffer)
5. If unsure, create a simple label: d += e.Dot().label("Diagram")
"""

        if custom_prompt:
            prompt += f"\nSpecial instructions: {custom_prompt}"

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
        detected_library = library_name

        lines = content.split('\n')
        code_lines = []
        in_code = False
        
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
            elif line.startswith('A.') and '.' in line:
                parts = line.split('.', 1)
                if len(parts) > 1:
                    options.append(parts[1].strip())
            elif line.startswith('B.') and '.' in line:
                parts = line.split('.', 1)
                if len(parts) > 1:
                    options.append(parts[1].strip())
            elif line.startswith('C.') and '.' in line:
                parts = line.split('.', 1)
                if len(parts) > 1:
                    options.append(parts[1].strip())
            elif line.startswith('D.') and '.' in line:
                parts = line.split('.', 1)
                if len(parts) > 1:
                    options.append(parts[1].strip())
            elif line.lower().startswith('answer:') and ':' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    correct_answer = parts[1].strip()
            elif line.lower().startswith('explanation:') and ':' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    explanation = parts[1].strip()
            elif line.lower().startswith('library:') and ':' in line:
                parts = line.split(':', 1)
                if len(parts) > 1:
                    detected_library = parts[1].strip()
            elif '```python' in line:
                in_code = True
            elif '```' in line and in_code:
                in_code = False
            elif in_code:
                code_lines.append(line)
                
        if code_lines:
            diagram_code = '\n'.join(code_lines)

        # Debug prints for parsed values
        print("Parsed question_text:", question_text)
        print("Parsed options:", options)
        print("Parsed correct_answer:", correct_answer)
        print("Parsed explanation:", explanation)

        # After parsing
        # (Revert: do not wrap math, just return as parsed)
        # question_text = wrap_math_latex(question_text)
        # options = [wrap_math_latex(opt) for opt in options if opt]
        # if explanation:
        #     explanation = wrap_math_latex(explanation)

        return {
            'question_text': question_text,
            'options': options,
            'correct_answer': correct_answer,
            'explanation': explanation,
            'diagram_code': diagram_code,
            'library_used': detected_library
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
            'library_used': 'schemdraw'
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
    """Get library-specific prompt instructions"""
    prompts = {
        'schemdraw': """import schemdraw
import schemdraw.elements as e
import schemdraw.flow as flow
import schemdraw.logic as logic
from schemdraw import Drawing

# Create a schemdraw diagram
d = Drawing()
# Add elements and save to buffer
d.save(buffer)""",
        
        'matplotlib': """import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from io import BytesIO

# Create matplotlib figure
fig, ax = plt.subplots(figsize=(8, 6))
# Add your plot elements here
# Example: ax.plot(x, y), ax.scatter(x, y), etc.
plt.savefig(buffer, format='png', bbox_inches='tight')
plt.close()""",
        
        'networkx': """import networkx as nx
import matplotlib.pyplot as plt
from io import BytesIO

# Create network graph
G = nx.Graph()
# Add nodes and edges
# Example: G.add_node(1), G.add_edge(1, 2)
nx.draw(G, with_labels=True)
plt.savefig(buffer, format='png', bbox_inches='tight')
plt.close()""",
        
        'graphviz': """import graphviz
from io import BytesIO

# Create graphviz diagram
dot = graphviz.Digraph()
# Add nodes and edges
# Example: dot.node('A', 'Node A'), dot.edge('A', 'B')
# Note: dot.render() saves to file, not buffer
dot.render('temp', format='png', cleanup=True)
# The backend will handle reading the file and serving the image""",
        
        'plotly': """import plotly.graph_objects as go
import plotly.io as pio
from io import BytesIO

# Create plotly figure
fig = go.Figure()
# Add traces and layout
# Example: fig.add_trace(go.Scatter(x=x, y=y))
pio.write_image(fig, buffer, format='png')""",
        
        'seaborn': """import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from io import BytesIO

# Create seaborn plot
# Example: sns.scatterplot(data=df, x='x', y='y')
# Example: sns.barplot(data=df, x='category', y='value')
# Example: sns.histplot(data=df, x='values')
plt.savefig(buffer, format='png', bbox_inches='tight')
plt.close()""",
        
        'pillow': """from PIL import Image, ImageDraw
from io import BytesIO

# Create PIL image
img = Image.new('RGB', (400, 300), color='white')
draw = ImageDraw.Draw(img)
# Add shapes and text
# Example: draw.rectangle([10, 10, 100, 100], outline='black')
img.save(buffer, format='PNG')""",
        
        'turtle': """import turtle
from io import BytesIO

# Create turtle drawing
t = turtle.Turtle()
screen = turtle.Screen()
# Add turtle commands
# Example: t.forward(100), t.right(90)
screen.getcanvas().postscript(file=buffer)
screen.bye()"""
    }
    
    return prompts.get(library_name, prompts['schemdraw'])

def get_library_rules(library_name):
    """Get library-specific rules"""
    rules = {
        'schemdraw': """1. Use ONLY valid schemdraw elements: e.Resistor2(), e.Capacitor2(), e.Inductor2(), logic.And(), logic.Or(), logic.Not(), flow.Start(), flow.Process(), flow.Decision(), flow.End()
2. NEVER use: e.AND2, e.OR2, e.LINE, or any non-existent elements
3. Use proper syntax: d += element_name()
4. Always end with: d.save(buffer)
5. If unsure, create a simple label: d += e.Dot().label("Diagram")""",
        
        'matplotlib': """1. Always import matplotlib.pyplot as plt, numpy as np, pandas as pd
2. Always create fig, ax = plt.subplots()
3. Use ax.plot(), ax.scatter(), ax.bar() for different plot types
4. NEVER use plt.show() - use plt.savefig() instead
5. Always end with: plt.savefig(buffer, format='png', bbox_inches='tight')
6. Always close with: plt.close()
7. Use clear, descriptive labels and titles""",
        
        'networkx': """1. Create graph with: G = nx.Graph() or G = nx.DiGraph()
2. Add nodes with: G.add_node(node_id)
3. Add edges with: G.add_edge(node1, node2)
4. Always end with: nx.draw(G, with_labels=True) and plt.savefig(buffer)
5. Always close with: plt.close()""",
        
        'graphviz': """1. Create diagram with: dot = graphviz.Digraph()
2. Add nodes with: dot.node('id', 'label')
3. Add edges with: dot.edge('from_id', 'to_id')
4. IMPORTANT: Use dot.render('temp', format='png', cleanup=True) - NOT buffer
5. Use clear node labels and edge labels
6. Graphviz saves to file, not buffer""",
        
        'plotly': """1. Create figure with: fig = go.Figure()
2. Add traces with: fig.add_trace(go.Scatter()), fig.add_trace(go.Bar()), etc.
3. Always end with: pio.write_image(fig, buffer, format='png')
4. Use clear titles and labels
5. Set appropriate layout with: fig.update_layout()""",
        
        'seaborn': """1. Import seaborn as sns and matplotlib.pyplot as plt
2. ALWAYS import pandas as pd and numpy as np
3. Use sns.scatterplot(), sns.lineplot(), sns.barplot(), sns.histplot() for different plots
4. NEVER use sns.venn2() or sns.venn3() - these don't exist
5. Always end with: plt.savefig(buffer, format='png', bbox_inches='tight')
6. Always close with: plt.close()
7. Use clear titles and labels""",
        
        'pillow': """1. Create image with: img = Image.new('RGB', (width, height), color='white')
2. Create draw object with: draw = ImageDraw.Draw(img)
3. Use draw.rectangle(), draw.circle(), draw.text() for shapes and text
4. Always end with: img.save(buffer, format='PNG')
5. Use clear colors and readable text""",
        
        'turtle': """1. Create turtle with: t = turtle.Turtle()
2. Create screen with: screen = turtle.Screen()
3. Use t.forward(), t.right(), t.left() for movement
4. Always end with: screen.getcanvas().postscript(file=buffer)
5. Always close with: screen.bye()"""
    }
    
    return rules.get(library_name, rules['schemdraw']) 