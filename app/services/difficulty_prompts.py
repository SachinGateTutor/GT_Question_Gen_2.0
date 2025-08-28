"""
Difficulty-specific prompt generation for question creation
This module provides prompts tailored to different difficulty levels
"""

def get_difficulty_criteria(difficulty_level):
    """Get specific criteria for a difficulty level"""
    criteria = {
        'Easy': {
            'description': 'EASY - Foundational concepts, direct recall, basic operations',
            'characteristics': [
                'Based on foundational definitions and standard formulas',
                'Involves direct recall or textbook-level facts',
                'One-step operations or straightforward logic',
                'Code questions: basic loops, conditionals, syntax',
                'Math questions: direct substitution into formulas',
                'Medical questions: naming, labeling, recalling symptoms',
                'Business questions: terminology or common models',
                'Distractor options are simple but relevant',
                'Time to solve: < 30 seconds'
            ],
            'examples': [
                'What is the time complexity of linear search?',
                'Which data structure uses LIFO principle?',
                'Define what a neural network is.',
                'What is the formula for calculating mean?'
            ]
        },
        'Medium': {
            'description': 'MEDIUM - Moderate complexity, multi-step reasoning',
            'characteristics': [
                'Requires 2–3 layers of reasoning or interpretation',
                'Involves moderate complexity in formulas, code, or case scenarios',
                'May require choosing the best method or tracing a function',
                'Introduces real-world context or slightly abstract reasoning',
                'Distractors are designed based on common errors/misconceptions',
                'Encourages problem-solving rather than recall',
                'May require calculating values from diagrams',
                'Time to solve: 1–2 minutes'
            ],
            'examples': [
                'Which sorting algorithm would be most efficient for nearly sorted data?',
                'How would you implement a queue using two stacks?',
                'Analyze the trade-offs between different activation functions.',
                'What are the implications of using different normalization techniques?'
            ]
        },
        'Hard': {
            'description': 'HARD - Advanced reasoning, multiple concepts, edge cases',
            'characteristics': [
                'Demands advanced reasoning and integration of multiple concepts',
                'Involves edge cases or exception handling',
                'Questions may involve ambiguous scenarios or optimization problems',
                'Algorithm analysis or trade-offs in decisions',
                'Diagrams may be complex with multiple elements',
                'All options are highly plausible with nuanced distinctions',
                'Explores corner cases, uncommon logic, or advanced use cases',
                'Time to solve: 2–4 minutes'
            ],
            'examples': [
                'Design an algorithm to find the shortest path in a weighted graph with negative edges.',
                'Analyze the space-time complexity trade-offs in a distributed system.',
                'Evaluate the impact of different regularization techniques on model generalization.',
                'Compare the performance characteristics of different neural network architectures.'
            ]
        },
        'Expert': {
            'description': 'EXPERT - Deep expertise, complex scenarios, cutting-edge concepts',
            'characteristics': [
                'Requires deep domain expertise and multiple concept integration',
                'Involves complex scenarios or optimization challenges',
                'May require creative solutions or novel approaches',
                'Cutting-edge concepts or advanced problem-solving',
                'Highly nuanced distinctions between options',
                'May involve research-level concepts',
                'Requires synthesis of multiple advanced topics',
                'Time to solve: 4+ minutes'
            ],
            'examples': [
                'Design a novel neural architecture for multi-modal learning.',
                'Develop an algorithm for real-time anomaly detection in streaming data.',
                'Create a system for automated code review with explainable AI.',
                'Design a distributed consensus protocol for blockchain applications.'
            ]
        }
    }
    return criteria.get(difficulty_level, criteria['Medium'])

def generate_difficulty_specific_prompt(topic, subject, stream, question_type, difficulty_level, library_name=None, requires_diagram=False):
    """Generate a prompt tailored to the specific difficulty level"""
    
    criteria = get_difficulty_criteria(difficulty_level)
    
    # Base prompt structure
    base_prompt = f"""
Generate a {difficulty_level.upper()} difficulty question for the topic '{topic}' in the subject '{subject}' for {stream} students.

{difficulty_level.upper()} DIFFICULTY CRITERIA:
{chr(10).join(f"• {char}" for char in criteria['characteristics'])}

EXAMPLES OF {difficulty_level.upper()} QUESTIONS:
{chr(10).join(f"• {example}" for example in criteria['examples'])}

REQUIREMENTS:
- Question must match the {difficulty_level} difficulty criteria above
- All options should be plausible but with clear distinctions
- Explanation should be comprehensive and educational
- Code examples should be appropriate for the difficulty level
"""

    # Add diagram-specific requirements if needed
    if requires_diagram and library_name:
        base_prompt += f"""
DIAGRAM REQUIREMENTS:
- Use {library_name} library for visualization
- Diagram should illustrate the key concepts clearly
- Complexity should match the {difficulty_level} difficulty level
- Include appropriate labels and annotations
"""

    # Add subject-specific requirements
    if subject.lower() in ['computer science', 'programming', 'data structures']:
        base_prompt += """
COMPUTER SCIENCE SPECIFIC:
- Focus on algorithms, data structures, or programming concepts
- Include code snippets or pseudocode where appropriate
- Consider time/space complexity for harder difficulties
- Emphasize practical implementation considerations
"""
    elif subject.lower() in ['mathematics', 'statistics']:
        base_prompt += """
MATHEMATICS SPECIFIC:
- Include mathematical notation and formulas
- Focus on problem-solving approaches
- Consider computational complexity
- Emphasize mathematical reasoning
"""
    elif subject.lower() in ['machine learning', 'artificial intelligence']:
        base_prompt += """
MACHINE LEARNING SPECIFIC:
- Focus on ML/AI concepts and algorithms
- Consider model performance and evaluation
- Include practical considerations
- Emphasize understanding of underlying principles
"""

    return base_prompt

def get_difficulty_validation_prompt(difficulty_level):
    """Generate a prompt to validate if a question matches the difficulty level"""
    
    criteria = get_difficulty_criteria(difficulty_level)
    
    return f"""
Validate if the following question matches {difficulty_level.upper()} difficulty criteria:

{difficulty_level.upper()} CRITERIA:
{chr(10).join(f"• {char}" for char in criteria['characteristics'])}

Analyze the question and respond with:
1. DIFFICULTY_MATCH: [YES/NO] - Does it match {difficulty_level} criteria?
2. REASONING: [Brief explanation of why it matches or doesn't match]
3. SUGGESTIONS: [Specific suggestions to adjust difficulty if needed]

Question to validate:
"""

def get_difficulty_adjustment_prompt(current_difficulty, target_difficulty):
    """Generate a prompt to adjust question difficulty"""
    
    current_criteria = get_difficulty_criteria(current_difficulty)
    target_criteria = get_difficulty_criteria(target_difficulty)
    
    return f"""
Adjust the following question from {current_difficulty.upper()} to {target_difficulty.upper()} difficulty.

CURRENT ({current_difficulty.upper()}) CRITERIA:
{chr(10).join(f"• {char}" for char in current_criteria['characteristics'])}

TARGET ({target_difficulty.upper()}) CRITERIA:
{chr(10).join(f"• {char}" for char in target_criteria['characteristics'])}

Provide the adjusted question that meets the {target_difficulty.upper()} criteria while maintaining the same core topic.
""" 