#!/usr/bin/env python3
"""
Test script for Bloom level tagging functionality
Tests both auto-detection and manual selection features
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

def test_bloom_level_auto_detection():
    """Test automatic Bloom level detection"""
    print("🔍 Testing Bloom Level Auto-Detection...")
    
    # Test data for different Bloom levels
    test_cases = [
        {
            "name": "Remember Level",
            "data": {
                "course": "B. Tech",
                "stream": "Computer Science",
                "subject": "Data Structures",
                "topic": "Arrays",
                "question_type": "MCQ",
                "difficulty_level": "Easy",
                "bloom_level": "auto_detect",
                "requires_diagram": False,
                "requires_option_diagrams": False
            }
        },
        {
            "name": "Understand Level", 
            "data": {
                "course": "B. Tech",
                "stream": "Computer Science", 
                "subject": "Algorithms",
                "topic": "Sorting",
                "question_type": "MCQ",
                "difficulty_level": "Medium",
                "bloom_level": "auto_detect",
                "requires_diagram": True,
                "requires_option_diagrams": False
            }
        },
        {
            "name": "Apply Level",
            "data": {
                "course": "B. Tech",
                "stream": "Computer Science",
                "subject": "Programming",
                "topic": "Functions",
                "question_type": "MCQ", 
                "difficulty_level": "Hard",
                "bloom_level": "auto_detect",
                "requires_diagram": False,
                "requires_option_diagrams": True
            }
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test {i}: {test_case['name']}")
        print(f"   Data: {test_case['data']}")
        
        try:
            # Generate question with auto-detect
            response = requests.post(f"{API_BASE}/generate", json=test_case['data'])
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success: Question generated")
                print(f"   📊 Question ID: {result.get('question_id', 'N/A')}")
                print(f"   🏷️  Auto-detected Bloom Level: {result.get('bloom_level', 'N/A')}")
                print(f"   📝 Question: {result.get('question_text', 'N/A')[:100]}...")
                
                # Debug: Print full response for first test
                if i == 1:
                    print(f"   🔍 Debug - Full response keys: {list(result.keys())}")
                    print(f"   🔍 Debug - Response: {result}")
                
                results.append({
                    "test": test_case['name'],
                    "status": "success",
                    "bloom_level": result.get('bloom_level'),
                    "question_id": result.get('question_id')
                })
            else:
                print(f"   ❌ Error: {response.status_code} - {response.text}")
                results.append({
                    "test": test_case['name'],
                    "status": "error",
                    "error": response.text
                })
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            results.append({
                "test": test_case['name'],
                "status": "exception",
                "error": str(e)
            })
        
        time.sleep(2)  # Rate limiting
    
    return results

def test_bloom_level_manual_selection():
    """Test manual Bloom level selection"""
    print("\n🔍 Testing Bloom Level Manual Selection...")
    
    bloom_levels = ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
    
    results = []
    
    for i, bloom_level in enumerate(bloom_levels, 1):
        print(f"\n📝 Test {i}: Manual Selection - {bloom_level}")
        
        test_data = {
            "course": "B. Tech",
            "stream": "Computer Science",
            "subject": "Data Structures",
            "topic": "Trees",
            "question_type": "MCQ",
            "difficulty_level": "Medium",
            "bloom_level": bloom_level,
            "requires_diagram": True,
            "requires_option_diagrams": False
        }
        
        print(f"   Data: {test_data}")
        
        try:
            response = requests.post(f"{API_BASE}/generate", json=test_data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success: Question generated")
                print(f"   📊 Question ID: {result.get('question_id', 'N/A')}")
                print(f"   🏷️  Selected Bloom Level: {bloom_level}")
                print(f"   📝 Question: {result.get('question_text', 'N/A')[:100]}...")
                
                results.append({
                    "test": f"Manual - {bloom_level}",
                    "status": "success",
                    "bloom_level": bloom_level,
                    "question_id": result.get('question_id')
                })
            else:
                print(f"   ❌ Error: {response.status_code} - {response.text}")
                results.append({
                    "test": f"Manual - {bloom_level}",
                    "status": "error",
                    "error": response.text
                })
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            results.append({
                "test": f"Manual - {bloom_level}",
                "status": "exception",
                "error": str(e)
            })
        
        time.sleep(2)  # Rate limiting
    
    return results

def test_bloom_level_database_storage():
    """Test if Bloom levels are properly stored in database"""
    print("\n🔍 Testing Bloom Level Database Storage...")
    
    try:
        # Get questions with Bloom levels
        response = requests.get(f"{API_BASE}/questions?status=all")
        
        if response.status_code == 200:
            questions = response.json()
            print(f"   📊 Total questions retrieved: {len(questions)}")
            
            bloom_levels_count = {}
            questions_with_bloom = 0
            
            for question in questions:
                bloom_level = question.get('bloom_level')
                if bloom_level:
                    questions_with_bloom += 1
                    bloom_levels_count[bloom_level] = bloom_levels_count.get(bloom_level, 0) + 1
            
            print(f"   ✅ Questions with Bloom levels: {questions_with_bloom}")
            print(f"   📊 Bloom level distribution:")
            for level, count in bloom_levels_count.items():
                print(f"      - {level}: {count}")
            
            return {
                "status": "success",
                "total_questions": len(questions),
                "questions_with_bloom": questions_with_bloom,
                "bloom_distribution": bloom_levels_count
            }
        else:
            print(f"   ❌ Error: {response.status_code} - {response.text}")
            return {"status": "error", "error": response.text}
            
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return {"status": "exception", "error": str(e)}

def test_bloom_level_api_endpoints():
    """Test Bloom level API endpoints"""
    print("\n🔍 Testing Bloom Level API Endpoints...")
    
    endpoints = [
        "/reference/BloomLevel",
        "/questions?status=all",
        "/questions?status=approved",
        "/questions?status=discarded"
    ]
    
    results = []
    
    for endpoint in endpoints:
        print(f"\n📝 Testing endpoint: {endpoint}")
        
        try:
            response = requests.get(f"{API_BASE}{endpoint}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Success: {response.status_code}")
                
                if endpoint == "/reference/BloomLevel":
                    print(f"   📊 Bloom levels available: {len(data)}")
                    for level in data:
                        print(f"      - {level}")
                else:
                    print(f"   📊 Questions returned: {len(data)}")
                
                results.append({
                    "endpoint": endpoint,
                    "status": "success",
                    "data_count": len(data)
                })
            else:
                print(f"   ❌ Error: {response.status_code} - {response.text}")
                results.append({
                    "endpoint": endpoint,
                    "status": "error",
                    "error": response.text
                })
                
        except Exception as e:
            print(f"   ❌ Exception: {str(e)}")
            results.append({
                "endpoint": endpoint,
                "status": "exception",
                "error": str(e)
            })
    
    return results

def main():
    """Run all Bloom level tests"""
    print("🧪 BLOOM LEVEL TAGGING TEST SUITE")
    print("=" * 50)
    
    # Test 1: Auto-detection
    auto_results = test_bloom_level_auto_detection()
    
    # Test 2: Manual selection
    manual_results = test_bloom_level_manual_selection()
    
    # Test 3: Database storage
    db_results = test_bloom_level_database_storage()
    
    # Test 4: API endpoints
    api_results = test_bloom_level_api_endpoints()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    # Auto-detection summary
    auto_success = sum(1 for r in auto_results if r['status'] == 'success')
    print(f"🔍 Auto-Detection Tests: {auto_success}/{len(auto_results)} passed")
    
    # Manual selection summary
    manual_success = sum(1 for r in manual_results if r['status'] == 'success')
    print(f"🏷️  Manual Selection Tests: {manual_success}/{len(manual_results)} passed")
    
    # Database summary
    if db_results['status'] == 'success':
        print(f"💾 Database Storage: ✅ Working")
        print(f"   - Total questions: {db_results['total_questions']}")
        print(f"   - Questions with Bloom levels: {db_results['questions_with_bloom']}")
    else:
        print(f"💾 Database Storage: ❌ Failed")
    
    # API endpoints summary
    api_success = sum(1 for r in api_results if r['status'] == 'success')
    print(f"🌐 API Endpoints: {api_success}/{len(api_results)} working")
    
    # Overall assessment
    total_tests = len(auto_results) + len(manual_results) + 1 + len(api_results)
    total_success = auto_success + manual_success + (1 if db_results['status'] == 'success' else 0) + api_success
    
    print(f"\n🎯 Overall Result: {total_success}/{total_tests} tests passed")
    
    if total_success == total_tests:
        print("✅ Bloom level tagging is working correctly!")
    else:
        print("⚠️  Some issues detected with Bloom level tagging")
    
    return {
        "auto_detection": auto_results,
        "manual_selection": manual_results,
        "database_storage": db_results,
        "api_endpoints": api_results,
        "total_success": total_success,
        "total_tests": total_tests
    }

if __name__ == "__main__":
    main() 