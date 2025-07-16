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

        # Check if this is a programming topic
        programming_topics = [
            'Java Programming', 'C++ Programming', 'Python Programming', 
            'Data Structures with Programs', 'Algorithms Implementation',
            'Object-Oriented Programming', 'Database Programming'
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

        lines = content.split('\n')
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

def generate_programming_question_prompt(topic, question_type, custom_prompt):
    """Generate a prompt for programming questions with code snippets"""
    
    import random
    import time
    
    # Create a seed based on current time to ensure different questions
    random.seed(time.time())
    timestamp_variation = int(time.time() * 1000) % 1000
    
    # Different programming question types
    programming_question_types = [
        "What will be the output of the following code?",
        "Identify the error in the given code snippet",
        "What is the time complexity of the following algorithm?",
        "Which of the following is the correct output?",
        "What will happen when this code is executed?",
        "Identify the data structure used in the code",
        "What is the purpose of the following code?",
        "Which statement about the code is correct?"
    ]
    
    selected_question_type = random.choice(programming_question_types)
    
    # Determine programming language based on topic
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
"""
    
    if custom_prompt:
        prompt += f"\nSpecial instructions: {custom_prompt}"
    
    return prompt

def generate_diagram_question_prompt(topic, subject, stream, question_type, requires_option_diagrams, library_name, custom_prompt):
    """Generate a prompt for diagram-based questions"""
    
    import random
    import time
    
    # Create a seed based on current time to ensure different questions
    random.seed(time.time())
    timestamp_variation = int(time.time() * 1000) % 1000
    
    option_diagram_instructions = ""
    if requires_option_diagrams:
        option_diagram_instructions = f"""

IMPORTANT: You must generate 4 separate diagrams for options A, B, C, and D.
Each option should have its own unique diagram that represents the concept described in that option.

For each option, provide a separate PythonCode block:
OptionACode:
```python
# Generate diagram for Option A
{get_library_specific_prompt(library_name)}
```

OptionBCode:
```python
# Generate diagram for Option B
{get_library_specific_prompt(library_name)}
```

OptionCCode:
```python
# Generate diagram for Option C
{get_library_specific_prompt(library_name)}
```

OptionDCode:
```python
# Generate diagram for Option D
{get_library_specific_prompt(library_name)}
```

CRITICAL: Each option diagram should be distinct and represent the concept described in that option.
"""

    # Different question types for variety
    question_types = [
        "Identify the data structure shown in the diagram",
        "Which of the following represents a [specific data structure]?",
        "What type of structure is illustrated below?",
        "Analyze the diagram and determine the data structure",
        "Based on the visual representation, what structure is this?",
        "Examine the diagram and identify the correct data structure",
        "What data structure is being demonstrated here?",
        "Which structure matches the given diagram?"
    ]
    
    # Different data structures for variety
    data_structures = [
        "Stack", "Queue", "Binary Tree", "Linked List", "Binary Search Tree",
        "Heap", "Graph", "Array", "Hash Table", "Tree", "AVL Tree",
        "Red-Black Tree", "B-Tree", "Trie", "Skip List", "Circular Queue",
        "Priority Queue", "Deque", "Doubly Linked List", "Circular Linked List"
    ]
    
    selected_question_type = random.choice(question_types)
    selected_data_structures = random.sample(data_structures, 4)
    variation_instruction = f"Use variation {timestamp_variation} to ensure uniqueness."
    
    prompt = f"""
Generate a {question_type} question for the topic '{topic}' in the subject '{subject}' ({stream} stream).

The question MUST include a relevant diagram using the {library_name} library.
{option_diagram_instructions}

IMPORTANT REQUIREMENTS FOR DIVERSITY:
1. Use this specific question format: "{selected_question_type}"
2. Make sure each option represents a different data structure concept
3. Include specific data structure names in options: {', '.join(selected_data_structures)}
4. Create unique and distinct diagrams for each option
5. Vary the complexity and structure of each diagram
6. Use different node labels, connections, and layouts for each option
7. {variation_instruction}

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
A. <option A text with specific data structure name>
B. <option B text with specific data structure name>
C. <option C text with specific data structure name>
D. <option D text with specific data structure name>
Answer: <correct option letter>
Explanation: <detailed, step-by-step explanation showing all intermediate steps, formulas, and reasoning, using LaTeX for all math. The explanation should be easy to understand, similar to a worked-out solution in a textbook.>
Library: {library_name}
PythonCode:
```python
# Generate diagram using {library_name}
{get_library_specific_prompt(library_name)}
```

CRITICAL RULES for the PythonCode:
{get_library_rules(library_name)}
"""
    
    if custom_prompt:
        prompt += f"\nSpecial instructions: {custom_prompt}"
    
    return prompt

def generate_regular_question_prompt(topic, subject, stream, question_type, custom_prompt):
    """Generate a prompt for regular questions without diagrams"""
    
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
Explanation: <detailed, step-by-step explanation showing all intermediate steps, formulas, and reasoning, using LaTeX for all math. The explanation should be easy to understand, similar to a worked-out solution in a textbook.>
"""
    
    if custom_prompt:
        prompt += f"\nSpecial instructions: {custom_prompt}"
    
    return prompt 

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
        
        # Extract options
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
        
        # Extract option diagram codes
        option_codes = ['OptionACode:', 'OptionBCode:', 'OptionCCode:', 'OptionDCode:']
        option_labels = ['A', 'B', 'C', 'D']
        
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
                option_diagram_codes[option_label] = '\n'.join(option_code_lines)
        
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