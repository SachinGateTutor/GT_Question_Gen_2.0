#!/usr/bin/env python3
"""
Complete System Test for AI MCQ Generator with Database Integration
"""

import sys
import os
import requests
import json

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_database_connection():
    """Test database connection"""
    print("🔍 Testing database connection...")
    try:
        from services.db_service import get_subjects, get_reference_data
        subjects = get_subjects()
        print(f"✅ Database connection successful! Found {len(subjects)} subjects")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\n🌐 Testing API endpoints...")
    base_url = "http://localhost:5000"
    
    endpoints = [
        "/api/subjects",
        "/api/reference/QuestionType",
        "/api/reference/BloomLevel",
        "/api/reference/DifficultyLevel",
        "/api/questions"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {endpoint}: {len(data)} items")
            else:
                print(f"❌ {endpoint}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: {e}")

def test_question_generation():
    """Test question generation with database storage"""
    print("\n🤖 Testing question generation...")
    
    test_data = {
        "subject_id": 1,  # Mathematics
        "topic_id": 1,    # Calculus
        "question_type_id": 1,  # MCQ
        "difficulty_level_id": 2,  # Medium
        "bloom_level_id": 3,  # Apply
        "question_type": "MCQ",
        "requires_diagram": True,
        "custom_prompt": "Focus on derivatives and calculus concepts",
        "num_questions": 1
    }
    
    try:
        response = requests.post(
            "http://localhost:5000/api/generate",
            json=test_data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Question generation successful!")
            print(f"   Question: {result.get('question_text', 'N/A')[:100]}...")
            print(f"   Options: {len(result.get('options', []))} options")
            print(f"   Diagram: {'Yes' if result.get('diagram_image_url') else 'No'}")
            print(f"   Library: {result.get('library_used', 'N/A')}")
            return True
        else:
            print(f"❌ Question generation failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Question generation error: {e}")
        return False

def test_question_retrieval():
    """Test retrieving questions from database"""
    print("\n📋 Testing question retrieval...")
    
    try:
        response = requests.get("http://localhost:5000/api/questions?status=all")
        
        if response.status_code == 200:
            questions = response.json()
            print(f"✅ Retrieved {len(questions)} questions from database")
            
            if questions:
                latest_question = questions[0]
                print(f"   Latest question: {latest_question.get('QuestionText', 'N/A')[:100]}...")
                print(f"   Subject: {latest_question.get('SubjectName', 'N/A')}")
                print(f"   Topic: {latest_question.get('TopicName', 'N/A')}")
                print(f"   Status: {'Approved' if latest_question.get('IsEnable') else 'Pending'}")
            
            return True
        else:
            print(f"❌ Question retrieval failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Question retrieval error: {e}")
        return False

def main():
    print("🚀 Complete System Test for AI MCQ Generator")
    print("=" * 60)
    
    # Test database connection
    if not test_database_connection():
        print("\n❌ Database test failed. Please check your SQL Server connection.")
        return
    
    # Test API endpoints
    test_api_endpoints()
    
    # Test question generation
    if test_question_generation():
        print("\n✅ Question generation test passed!")
    else:
        print("\n❌ Question generation test failed!")
    
    # Test question retrieval
    if test_question_retrieval():
        print("\n✅ Question retrieval test passed!")
    else:
        print("\n❌ Question retrieval test failed!")
    
    print("\n🎉 System test completed!")
    print("\n📋 Next steps:")
    print("   1. Open http://localhost:5000 in your browser")
    print("   2. Try generating questions with the new UI")
    print("   3. Visit the review page to approve/discard questions")
    print("   4. Check your database to see stored questions")

if __name__ == "__main__":
    main() 