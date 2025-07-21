#!/usr/bin/env python3
"""
Test script for programming questions feature
"""

import requests
import json

def test_programming_question():
    """Test generating a programming question"""
    
    # Test data for programming question
    test_data = {
        "course_id": 1,
        "stream_id": 1, 
        "subject_id": 1,
        "topic_id": 1,
        "question_type_id": 1,
        "difficulty_level_id": 1,
        "bloom_level_id": 1,
        "question_type": "MCQ",
        "requires_diagram": False,
        "requires_option_diagrams": False,
        "is_programming_question": True,
        "custom_prompt": "Generate a Java programming question about loops and output",
        "num_questions": 1
    }
    
    try:
        print("🧪 Testing programming question generation...")
        
        # Send request to the API
        response = requests.post(
            'http://localhost:5000/api/generate',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Programming question generated successfully!")
            print(f"📝 Question: {result.get('question_text', 'No question')[:100]}...")
            print(f"🔤 Options: {len(result.get('options', []))} options found")
            print(f"✅ Correct Answer: {result.get('correct_answer', 'None')}")
            print(f"📚 Explanation: {result.get('explanation', 'No explanation')[:100]}...")
            
            # Check if code snippet is present
            question_text = result.get('question_text', '')
            if '```' in question_text:
                print("💻 Code snippet detected in question!")
            else:
                print("⚠️ No code snippet found in question")
                
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error testing programming question: {str(e)}")

def test_regular_question():
    """Test generating a regular question for comparison"""
    
    test_data = {
        "course_id": 1,
        "stream_id": 1,
        "subject_id": 1,
        "topic_id": 1,
        "question_type_id": 1,
        "difficulty_level_id": 1,
        "bloom_level_id": 1,
        "question_type": "MCQ",
        "requires_diagram": False,
        "requires_option_diagrams": False,
        "is_programming_question": False,
        "custom_prompt": "Generate a regular data structure question",
        "num_questions": 1
    }
    
    try:
        print("\n🧪 Testing regular question generation...")
        
        response = requests.post(
            'http://localhost:5000/api/generate',
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Regular question generated successfully!")
            print(f"📝 Question: {result.get('question_text', 'No question')[:100]}...")
            
            # Check that no code snippet is present
            question_text = result.get('question_text', '')
            if '```' not in question_text:
                print("✅ No code snippet in regular question (as expected)")
            else:
                print("⚠️ Code snippet found in regular question (unexpected)")
                
        else:
            print(f"❌ Error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing regular question: {str(e)}")

if __name__ == "__main__":
    print("🚀 Starting Programming Questions Test Suite")
    print("=" * 50)
    
    test_programming_question()
    test_regular_question()
    
    print("\n" + "=" * 50)
    print("✅ Test suite completed!")
    print("\n📋 Summary:")
    print("- Programming questions should include code snippets")
    print("- Regular questions should not include code snippets")
    print("- Both should generate valid MCQ questions")
    print("- Frontend should display code with syntax highlighting") 