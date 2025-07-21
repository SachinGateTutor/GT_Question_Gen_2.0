#!/usr/bin/env python3
"""
Test script to see raw AI response for programming questions
"""

import requests
import json

def test_raw_response():
    """Test to see the raw AI response"""
    
    # Test data for programming question
    test_data = {
        "course_id": 1,
        "stream_id": 1, 
        "subject_id": 15,  # Programming subject
        "topic_id": 48,    # Java Programming topic
        "question_type_id": 1,
        "difficulty_level_id": 3,
        "bloom_level_id": None,
        "question_type": "MCQ",
        "requires_diagram": False,
        "requires_option_diagrams": False,
        "is_programming_question": True,
        "custom_prompt": "Generate a Java programming question with a clear code snippet about loops",
        "num_questions": 1
    }
    
    try:
        print("🧪 Testing raw AI response...")
        
        # Send request to the API
        response = requests.post(
            'http://localhost:5000/api/generate',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API response received!")
            
            # Check if there are any questions with code snippets
            all_questions = result.get('all_questions', [])
            if all_questions:
                question = all_questions[0]
                question_text = question.get('question_text', '')
                
                print(f"📝 Question text: {question_text}")
                print(f"🔍 Question text contains '```': {'```' in question_text}")
                
                if '```' in question_text:
                    print("💻 Code snippet found in question text!")
                    # Extract and display the code snippet
                    import re
                    code_matches = re.findall(r'```(\w+)?\n(.*?)```', question_text, re.DOTALL)
                    for i, (lang, code) in enumerate(code_matches):
                        print(f"🔧 Code block {i+1} ({lang or 'text'}):")
                        print(code.strip())
                else:
                    print("⚠️ No code snippet found in question text")
                    
                    # Check if the question mentions code but doesn't have it
                    if any(word in question_text.lower() for word in ['code', 'output', 'snippet', 'program']):
                        print("🔍 Question mentions code but no snippet found - this indicates a parsing issue")
                
            else:
                print("⚠️ No questions in response")
                
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Testing Raw AI Response")
    print("=" * 50)
    
    test_raw_response()
    
    print("\n" + "=" * 50)
    print("✅ Test completed!") 