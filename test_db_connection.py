#!/usr/bin/env python3
"""
Test script to verify SQL Server database connection and basic operations
"""

import sys
import os

# Add the app directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.db_service import (
    get_db_connection, get_subjects, get_topics_by_subject, 
    get_reference_data
)

def test_database_connection():
    """Test basic database connectivity"""
    print("🔍 Testing database connection...")
    
    # Test connection
    conn = get_db_connection()
    if conn:
        print("✅ Database connection successful!")
        conn.close()
    else:
        print("❌ Database connection failed!")
        return False
    
    return True

def test_reference_data():
    """Test fetching reference data"""
    print("\n📊 Testing reference data retrieval...")
    
    # Test subjects
    subjects = get_subjects()
    print(f"✅ Found {len(subjects)} subjects:")
    for subject in subjects:
        print(f"   - {subject['SubjectName']} (ID: {subject['SubjectID']})")
    
    # Test topics for first subject
    if subjects:
        first_subject_id = subjects[0]['SubjectID']
        topics = get_topics_by_subject(first_subject_id)
        print(f"\n✅ Found {len(topics)} topics for subject {subjects[0]['SubjectName']}:")
        for topic in topics:
            print(f"   - {topic['TopicName']} (ID: {topic['TopicID']})")
    
    # Test reference tables
    reference_tables = ['QuestionType', 'BloomLevel', 'DifficultyLevel', 'SectionType']
    for table in reference_tables:
        data = get_reference_data(table)
        print(f"\n✅ Found {len(data)} records in {table}:")
        for item in data:
            if 'Name' in item:
                print(f"   - {item['Name']}")
            elif 'TypeName' in item:
                print(f"   - {item['TypeName']}")
            elif 'LevelName' in item:
                print(f"   - {item['LevelName']}")

def main():
    print("🚀 SQL Server Database Connection Test")
    print("=" * 50)
    
    # Test connection
    if not test_database_connection():
        print("\n❌ Database connection failed. Please check:")
        print("   1. SQL Server is running")
        print("   2. Database 'MCQGen' exists")
        print("   3. Connection string in db_service.py is correct")
        print("   4. Windows Authentication is enabled (or update credentials)")
        return
    
    # Test data retrieval
    test_reference_data()
    
    print("\n✅ All tests completed successfully!")
    print("\n📋 Next steps:")
    print("   1. Install pyodbc: pip install pyodbc")
    print("   2. Update connection string in app/services/db_service.py if needed")
    print("   3. Start the Flask server: python app/main.py")

if __name__ == "__main__":
    main() 