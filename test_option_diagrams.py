#!/usr/bin/env python3
"""
Test script for option diagram functionality
"""

import requests
import json

# Test configuration
API_URL = "http://localhost:5000/api/generate"

def test_option_diagrams():
    """Test the option diagram generation functionality"""
    
    # Test data
    test_data = {
        "course_id": 1,
        "stream_id": 1,
        "subject_id": 1,
        "topic_id": 1,
        "question_type_id": 1,
        "difficulty_level_id": None,
        "bloom_level_id": None,
        "question_type": "MCQ",
        "requires_diagram": True,
        "requires_option_diagrams": True,  # This is the new feature
        "custom_prompt": "Generate a question about binary trees with diagrams for each option",
        "num_questions": 1
    }
    
    print("🧪 Testing option diagram generation...")
    print(f"📤 Sending request to: {API_URL}")
    print(f"📋 Test data: {json.dumps(test_data, indent=2)}")
    
    try:
        # Send request
        response = requests.post(API_URL, json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Request successful!")
            print(f"📝 Question: {result.get('question_text', 'No question')}")
            print(f"🔤 Options: {result.get('options', [])}")
            print(f"✅ Correct Answer: {result.get('correct_answer', 'None')}")
            print(f"📊 Main Diagram: {result.get('diagram_image_url', 'None')}")
            print(f"🖼️ Option Images: {result.get('option_images', 'None')}")
            
            # Check if option images were generated
            option_images = result.get('option_images')
            if option_images:
                print("🎉 Option diagrams were generated!")
                for i, img in enumerate(option_images):
                    if img:
                        print(f"   Option {chr(65+i)}: {img}")
                    else:
                        print(f"   Option {chr(65+i)}: No image")
            else:
                print("❌ No option images were generated")
                
        else:
            print(f"❌ Request failed with status {response.status_code}")
            print(f"📄 Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error during test: {e}")

def test_text_only():
    """Test without option diagrams for comparison"""
    
    test_data = {
        "course_id": 1,
        "stream_id": 1,
        "subject_id": 1,
        "topic_id": 1,
        "question_type_id": 1,
        "difficulty_level_id": None,
        "bloom_level_id": None,
        "question_type": "MCQ",
        "requires_diagram": True,
        "requires_option_diagrams": False,  # No option diagrams
        "custom_prompt": "Generate a question about binary trees",
        "num_questions": 1
    }
    
    print("\n🧪 Testing text-only options (no option diagrams)...")
    
    try:
        response = requests.post(API_URL, json=test_data)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Text-only request successful!")
            print(f"📊 Main Diagram: {result.get('diagram_image_url', 'None')}")
            print(f"🖼️ Option Images: {result.get('option_images', 'None')}")
            
            option_images = result.get('option_images')
            if not option_images or all(img is None for img in option_images):
                print("✅ Correctly generated no option images")
            else:
                print("❌ Unexpected option images generated")
                
        else:
            print(f"❌ Text-only request failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error during text-only test: {e}")

if __name__ == "__main__":
    print("🚀 Starting option diagram tests...")
    test_option_diagrams()
    test_text_only()
    print("\n✨ Tests completed!") 