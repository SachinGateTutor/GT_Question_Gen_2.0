import os
import openai
import traceback

def get_openai_client():
    # Hardcoded API key for limited use
    api_key = "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"
    print(f"Debug: Using hardcoded API key: {api_key[:20]}...")
    print("Debug: Creating OpenAI client with valid API key")
    return openai.OpenAI(api_key=api_key)

def generate_mcq_and_diagram(data):
    try:
        stream = data.get('stream', 'CS')
        subject = data.get('subject', 'Data Structures')
        topic = data.get('topic', 'Binary Trees')
        question_type = data.get('question_type', 'MCQ')
        requires_diagram = data.get('requires_diagram', False)
        custom_prompt = data.get('custom_prompt', '')

        # Get OpenAI client
        client = get_openai_client()
        if not client:
            return {
                'error': 'OpenAI API key not set. Please add your API key to the .env file.',
                'question_text': 'Sample question for testing',
                'options': ['A', 'B', 'C', 'D'],
                'correct_answer': 'A',
                'explanation': 'This is a sample response for testing.',
                'diagram_code': None
            }

        prompt = f"""
Generate a {question_type} question for the topic '{topic}' in the subject '{subject}' ({stream} stream).

Format your response exactly as follows:

Question: <question text>
A. <option A>
B. <option B>
C. <option C>
D. <option D>
Answer: <correct option letter>
Explanation: <brief explanation>
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
        if requires_diagram:
            prompt += "\nThe question MUST include a relevant diagram for the topic using schemdraw. Do NOT skip the diagram."
        else:
            prompt += "\nIf a diagram is not required, you may use a minimal placeholder diagram."
        if custom_prompt:
            prompt += f"\nSpecial instructions: {custom_prompt}"

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content
        print("=== RAW OPENAI RESPONSE ===")
        print(content)
        print("===========================")

        # Improved parsing with better error handling
        question_text = None
        options = []
        correct_answer = None
        explanation = None
        diagram_code = None

        lines = content.split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            if line is None:
                continue
            line = line.strip()
            if not line:
                continue
                
            if line.lower().startswith('question:'):
                parts = line.split(':', 1)
                if len(parts) > 1:
                    question_text = parts[1].strip()
            elif line.startswith('A.'):
                parts = line.split('.', 1)
                if len(parts) > 1:
                    options.append(parts[1].strip())
            elif line.startswith('B.'):
                parts = line.split('.', 1)
                if len(parts) > 1:
                    options.append(parts[1].strip())
            elif line.startswith('C.'):
                parts = line.split('.', 1)
                if len(parts) > 1:
                    options.append(parts[1].strip())
            elif line.startswith('D.'):
                parts = line.split('.', 1)
                if len(parts) > 1:
                    options.append(parts[1].strip())
            elif line.lower().startswith('answer:'):
                parts = line.split(':', 1)
                if len(parts) > 1:
                    correct_answer = parts[1].strip()
            elif line.lower().startswith('explanation:'):
                parts = line.split(':', 1)
                if len(parts) > 1:
                    explanation = parts[1].strip()
            elif '```python' in line:
                in_code = True
            elif '```' in line and in_code:
                in_code = False
            elif in_code:
                code_lines.append(line)
                
        if code_lines:
            diagram_code = '\n'.join(code_lines)

        return {
            'question_text': question_text,
            'options': options,
            'correct_answer': correct_answer,
            'explanation': explanation,
            'diagram_code': diagram_code
        }
    except Exception as e:
        print(f"Error in OpenAI service: {e}")
        traceback.print_exc()
        return {
            'error': f'OpenAI API error: {str(e)}',
            'question_text': 'Sample question for testing',
            'options': ['A', 'B', 'C', 'D'],
            'correct_answer': 'A',
            'explanation': 'This is a sample response for testing.',
            'diagram_code': None
        } 