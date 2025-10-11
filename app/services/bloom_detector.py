import openai
import re
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_openai_client():
    """Get OpenAI client with API key from environment variables"""
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables. Please check your .env file.")
    
    return openai.OpenAI(api_key=api_key)

def detect_bloom_level(question_text, options, explanation):
    """
    Detect the Bloom level of a question using AI analysis
    
    Returns:
        int: Bloom level ID (1-6) or None if detection fails
    """
    
    # Bloom level definitions for AI analysis
    bloom_definitions = {
        1: {
            'name': 'Remember',
            'description': 'Retrieving relevant knowledge from long-term memory',
            'verbs': ['define', 'list', 'name', 'recall', 'recognize', 'label', 'identify', 'state', 'memorize'],
            'examples': ['What is the time complexity of binary search?', 'Define recursion']
        },
        2: {
            'name': 'Understand',
            'description': 'Constructing meaning from messages or instructional materials',
            'verbs': ['summarize', 'explain', 'describe', 'interpret', 'classify', 'paraphrase', 'compare', 'discuss'],
            'examples': ['Explain the concept of recursion with an example', 'Describe how a stack works']
        },
        3: {
            'name': 'Apply',
            'description': 'Carrying out or using a procedure in a given situation',
            'verbs': ['implement', 'use', 'execute', 'solve', 'demonstrate', 'modify', 'apply', 'calculate'],
            'examples': ['Write a function to check if a number is prime', 'Implement a binary search algorithm']
        },
        4: {
            'name': 'Analyze',
            'description': 'Breaking information into parts to understand its structure',
            'verbs': ['compare', 'contrast', 'categorize', 'investigate', 'examine', 'analyze', 'break down'],
            'examples': ['Analyze the output of this recursive function and explain the flow', 'Compare the efficiency of two sorting algorithms']
        },
        5: {
            'name': 'Evaluate',
            'description': 'Making judgments based on criteria or standards',
            'verbs': ['critique', 'justify', 'validate', 'recommend', 'assess', 'evaluate', 'judge'],
            'examples': ['Which sorting algorithm is most efficient for nearly sorted data and why?', 'Evaluate the trade-offs between different data structures']
        },
        6: {
            'name': 'Create',
            'description': 'Putting elements together to form a novel, coherent whole or original product',
            'verbs': ['design', 'build', 'compose', 'develop', 'formulate', 'construct', 'create', 'invent'],
            'examples': ['Design a simple file storage system with metadata indexing', 'Create an algorithm to solve a specific problem']
        }
    }
    
    try:
        client = get_openai_client()
        
        # Create analysis prompt
        prompt = f"""
Analyze the following question and determine which Bloom's Taxonomy level it belongs to.

Question: {question_text}
Options: {', '.join(options)}
Explanation: {explanation}

Bloom's Taxonomy Levels:
"""
        
        for level_id, level_info in bloom_definitions.items():
            prompt += f"""
{level_id}. {level_info['name']}
   Definition: {level_info['description']}
   Key Verbs: {', '.join(level_info['verbs'])}
   Examples: {', '.join(level_info['examples'])}
"""
        
        prompt += """
Based on the question content, options, and explanation, determine the most appropriate Bloom level.
Consider:
1. The cognitive skills required to answer the question
2. The verbs used in the question
3. The complexity of the task
4. The type of thinking required

Respond with ONLY the Bloom level number (1-6) and a brief justification.
Format: Level: X
Justification: [brief explanation]
"""
        
        # Import the hybrid model selection function
        from .openai_service import select_optimal_model
        
        # Use hybrid model selection for Bloom detection
        complexity_factors = {
            'subject': 'General',  # Bloom detection is subject-agnostic
            'topic': 'General'
        }
        selected_model, model_reason = select_optimal_model('bloom_detection', complexity_factors)
        
        response = client.chat.completions.create(
            model=selected_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        
        content = response.choices[0].message.content.strip()
        
        # Extract level number
        level_match = re.search(r'Level:\s*(\d+)', content, re.IGNORECASE)
        if level_match:
            level = int(level_match.group(1))
            if 1 <= level <= 6:
                print(f"🔍 Bloom Level Detected: {level} ({bloom_definitions[level]['name']})")
                return level
        
        # Fallback: try to find level number anywhere in response
        level_match = re.search(r'\b([1-6])\b', content)
        if level_match:
            level = int(level_match.group(1))
            print(f"🔍 Bloom Level Detected (fallback): {level} ({bloom_definitions[level]['name']})")
            return level
        
        print(f"❌ Could not detect Bloom level from response: {content}")
        return None
        
    except Exception as e:
        print(f"❌ Error detecting Bloom level: {e}")
        return None

def update_question_bloom_level(question_id, bloom_level_id):
    """
    Update the Bloom level for a question in the database
    
    Args:
        question_id (int): The question ID
        bloom_level_id (int): The detected Bloom level ID
    """
    try:
        from .db_service import get_db_connection
        
        conn = get_db_connection()
        if not conn:
            print("❌ Database connection failed")
            return False
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE QuestionMaster 
            SET BloomLevelID = ? 
            WHERE QuestionID = ?
        """, (bloom_level_id, question_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"✅ Updated question {question_id} with Bloom level {bloom_level_id}")
        return True
        
    except Exception as e:
        print(f"❌ Error updating Bloom level: {e}")
        return False 