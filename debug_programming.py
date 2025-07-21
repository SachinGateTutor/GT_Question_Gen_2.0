#!/usr/bin/env python3
"""
Debug script for programming questions
"""

import requests
import json

def test_programming_api():
    """Test the programming questions API directly"""
    
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
        "custom_prompt": "Generate a Java programming question about loops and output",
        "num_questions": 1
    }
    
    try:
        print("🧪 Testing programming question API...")
        print(f"📤 Sending data: {json.dumps(test_data, indent=2)}")
        
        # Send request to the API
        response = requests.post(
            'http://localhost:5000/api/generate',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        print(f"📥 Response status: {response.status_code}")
        print(f"📥 Response headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ API response received!")
            print(f"📝 Question text: {result.get('question_text', 'No question')}")
            print(f"🔤 Options: {result.get('options', [])}")
            print(f"✅ Correct Answer: {result.get('correct_answer', 'None')}")
            print(f"📚 Explanation: {result.get('explanation', 'No explanation')[:100]}...")
            print(f"📊 Total generated: {result.get('total_generated', 0)}")
            print(f"📋 All questions: {len(result.get('all_questions', []))}")
            
            # Check if code snippet is present
            question_text = result.get('question_text', '')
            if '```' in question_text:
                print("💻 Code snippet detected in question!")
            else:
                print("⚠️ No code snippet found in question")
                
            # Print full response for debugging
            print("\n🔍 Full API Response:")
            print(json.dumps(result, indent=2))
                
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing programming question: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Programming Questions Debug")
    print("=" * 50)
    
    test_programming_api()
    
    print("\n" + "=" * 50)
    print("✅ Debug completed!") 