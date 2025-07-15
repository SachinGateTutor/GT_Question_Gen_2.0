#!/usr/bin/env python3
"""
Data Transfer Script for GT Question Generator 2.0
Transfers all generated data from current system to new system
"""

import pyodbc
import json
import os
from datetime import datetime

def get_source_connection():
    """Connect to source database (current system)"""
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=localhost;'
            'DATABASE=MCQGen;'
            'Trusted_Connection=yes;'
        )
        return conn
    except Exception as e:
        print(f"Error connecting to source database: {e}")
        return None

def get_target_connection():
    """Connect to target database (new system)"""
    try:
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=localhost;'
            'DATABASE=GTQuestionDB;'
            'Trusted_Connection=yes;'
        )
        return conn
    except Exception as e:
        print(f"Error connecting to target database: {e}")
        return None

def export_data_to_json(source_conn, filename):
    """Export all data to JSON file"""
    data = {}
    
    # Tables to export
    tables = [
        'CourseMaster', 'StreamMaster', 'SubjectMaster', 'TopicMaster',
        'QuestionType', 'BloomLevel', 'DifficultyLevel', 'SectionType',
        'QuestionMaster', 'MCQ_Questions', 'QuestionExplanation'
    ]
    
    for table in tables:
        try:
            cursor = source_conn.cursor()
            cursor.execute(f"SELECT * FROM {table}")
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            columns = [column[0] for column in cursor.description]
            table_data = []
            for row in rows:
                table_data.append(dict(zip(columns, row)))
            
            data[table] = table_data
            print(f"✅ Exported {len(table_data)} rows from {table}")
            
        except Exception as e:
            print(f"❌ Error exporting {table}: {e}")
    
    # Save to JSON file
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"📁 Data exported to: {filename}")
    return data

def import_data_from_json(target_conn, filename):
    """Import data from JSON file to target database"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error reading JSON file: {e}")
        return False
    
    # Import reference tables first (they have foreign key dependencies)
    reference_tables = [
        'CourseMaster', 'StreamMaster', 'SubjectMaster', 'TopicMaster',
        'QuestionType', 'BloomLevel', 'DifficultyLevel', 'SectionType'
    ]
    
    for table in reference_tables:
        if table in data:
            try:
                cursor = target_conn.cursor()
                
                # Clear existing data (optional)
                cursor.execute(f"DELETE FROM {table}")
                
                # Insert new data
                for row in data[table]:
                    columns = ', '.join(row.keys())
                    placeholders = ', '.join(['?' for _ in row])
                    values = list(row.values())
                    
                    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
                    cursor.execute(query, values)
                
                target_conn.commit()
                print(f"✅ Imported {len(data[table])} rows to {table}")
                
            except Exception as e:
                print(f"❌ Error importing {table}: {e}")
                target_conn.rollback()
    
    # Import main data tables
    main_tables = ['QuestionMaster', 'MCQ_Questions', 'QuestionExplanation']
    
    for table in main_tables:
        if table in data:
            try:
                cursor = target_conn.cursor()
                
                # Clear existing data (optional)
                cursor.execute(f"DELETE FROM {table}")
                
                # Insert new data
                for row in data[table]:
                    columns = ', '.join(row.keys())
                    placeholders = ', '.join(['?' for _ in row])
                    values = list(row.values())
                    
                    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
                    cursor.execute(query, values)
                
                target_conn.commit()
                print(f"✅ Imported {len(data[table])} rows to {table}")
                
            except Exception as e:
                print(f"❌ Error importing {table}: {e}")
                target_conn.rollback()
    
    return True

def copy_generated_images():
    """Copy generated images from source to target"""
    source_dir = "app/static/images"
    target_dir = "app/static/images"
    
    if not os.path.exists(source_dir):
        print(f"⚠️ Source images directory not found: {source_dir}")
        return
    
    if not os.path.exists(target_dir):
        os.makedirs(target_dir)
    
    copied_count = 0
    for filename in os.listdir(source_dir):
        if filename.endswith('.png'):
            source_path = os.path.join(source_dir, filename)
            target_path = os.path.join(target_dir, filename)
            
            try:
                import shutil
                shutil.copy2(source_path, target_path)
                copied_count += 1
            except Exception as e:
                print(f"❌ Error copying {filename}: {e}")
    
    print(f"✅ Copied {copied_count} image files")

def main():
    print("🔄 GT Question Generator - Data Transfer Tool")
    print("=" * 50)
    
    # Step 1: Export from source
    print("\n📤 Step 1: Exporting data from current system...")
    source_conn = get_source_connection()
    if not source_conn:
        print("❌ Cannot connect to source database")
        return
    
    export_filename = f"data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    data = export_data_to_json(source_conn, export_filename)
    source_conn.close()
    
    # Step 2: Import to target
    print("\n📥 Step 2: Importing data to new system...")
    target_conn = get_target_connection()
    if not target_conn:
        print("❌ Cannot connect to target database")
        return
    
    success = import_data_from_json(target_conn, export_filename)
    target_conn.close()
    
    # Step 3: Copy images
    print("\n🖼️ Step 3: Copying generated images...")
    copy_generated_images()
    
    if success:
        print("\n✅ Data transfer completed successfully!")
        print(f"📁 Export file: {export_filename}")
        print("🔧 You can now delete the export file if no longer needed")
    else:
        print("\n❌ Data transfer failed!")

if __name__ == "__main__":
    main() 