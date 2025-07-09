import pyodbc
import os
from datetime import datetime
import json
import re

def get_db_connection():
    """Get SQL Server database connection"""
    try:
        # Update these connection details with your actual SQL Server info
        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=localhost;'  # Change to your server name
            'DATABASE=MCQGen;'   # Your database name
            'Trusted_Connection=yes;'  # Windows Authentication
            # Or use SQL Authentication:
            # 'UID=your_username;'
            # 'PWD=your_password;'
        )
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def get_reference_data(table_name):
    """Get all records from a reference table"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        
        # Convert to list of dictionaries
        columns = [column[0] for column in cursor.description]
        result = []
        for row in rows:
            result.append(dict(zip(columns, row)))
        
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Error getting {table_name}: {e}")
        return []

def get_subjects():
    """Get all active subjects"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT SubjectID, SubjectName FROM SubjectMaster WHERE IsActive = 1")
        rows = cursor.fetchall()
        result = [{'SubjectID': row[0], 'SubjectName': row[1]} for row in rows]
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Error getting subjects: {e}")
        return []

def get_topics_by_subject(subject_id):
    """Get topics for a specific subject"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT TopicID, TopicName, BloomLevelID 
            FROM TopicMaster 
            WHERE SubjectID = ? AND IsActive = 1
        """, subject_id)
        rows = cursor.fetchall()
        result = [{'TopicID': row[0], 'TopicName': row[1], 'BloomLevelID': row[2]} for row in rows]
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Error getting topics: {e}")
        return []

def insert_question_master(data):
    conn = get_db_connection()
    if not conn:
        return None
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO QuestionMaster 
            (SubjectID, TopicID, QuestionTypeID, Marks, BloomLevelID, 
             DifficultyLevelID, SectionID, IsEnable, IsDeleted, IsPublic, AddedDate)
            OUTPUT INSERTED.QuestionID
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data['subject_id'],
            data['topic_id'],
            data['question_type_id'],
            data.get('marks', 1),
            data.get('bloom_level_id'),
            data.get('difficulty_level_id'),
            data.get('section_id'),
            0,  # IsEnable - default to false
            0,  # IsDeleted - default to false
            0,  # IsPublic - default to false
            datetime.now()
        ))
        result = cursor.fetchone()
        if result is None:
            return None
        question_id = result[0]
        conn.commit()
        cursor.close()
        conn.close()
        return int(question_id)
    except Exception as e:
        print(f"Error inserting question master: {e}")
        return None

def insert_mcq_question(question_id, data):
    print(f"insert_mcq_question called with question_id={question_id}")
    print(f"question_text: {data.get('question_text')}")
    print(f"options: {data.get('options')}")
    print(f"correct_answer: {data.get('correct_answer')}")
    print(f"diagram_image_url: {data.get('diagram_image_url')}")
    options = data.get('options') or []
    
    # Clean the correct answer to extract just the letter (A, B, C, D)
    correct_answer = data.get('correct_answer', '')
    if correct_answer:
        # Extract just the letter from answers like "B. 80%" or "B"
        match = re.search(r'^([A-D])', correct_answer.strip())
        if match:
            correct_answer = match.group(1)
        else:
            # If no letter found, try to find the correct option by matching
            for i, option in enumerate(options):
                if option in correct_answer:
                    correct_answer = chr(65 + i)  # Convert to A, B, C, D
                    break
            else:
                correct_answer = 'A'  # Default fallback
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO MCQ_Questions 
            (QuestionID, QuestionText, OptionA, OptionB, OptionC, OptionD, 
             CorrectOption, HasImage, ImgQuestion)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            question_id,
            data.get('question_text'),
            options[0] if len(options) > 0 else None,
            options[1] if len(options) > 1 else None,
            options[2] if len(options) > 2 else None,
            options[3] if len(options) > 3 else None,
            correct_answer,
            1 if data.get('diagram_image_url') else 0,
            data.get('diagram_image_url')
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error inserting MCQ question: {e}")
        return False

def insert_question_explanation(question_id, data):
    """Insert question explanation"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO QuestionExplanation 
            (QuestionID, ExplanationText, ImgExplanation, CreatedOn)
            VALUES (?, ?, ?, ?)
        """, (
            question_id,
            data.get('explanation'),
            data.get('diagram_image_url'),
            datetime.now()
        ))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error inserting explanation: {e}")
        return False

def store_generated_question(data):
    """Main function to store a generated question"""
    try:
        # Insert into QuestionMaster
        question_id = insert_question_master(data)
        if not question_id:
            return False
        
        # Insert into MCQ_Questions
        if not insert_mcq_question(question_id, data):
            return False
        
        # Insert explanation
        insert_question_explanation(question_id, data)
        
        return True
    except Exception as e:
        print(f"Error storing question: {e}")
        return False

def get_questions_by_status(status='pending', course='', stream='', subject='', topic='', difficulty='', bloom=''):
    """Get questions by status and additional filters"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        cursor = conn.cursor()
        
        # Build the base query with joins for course and stream
        query = """
            SELECT 
                qm.QuestionID,
                qm.SubjectID,
                qm.TopicID,
                qm.QuestionTypeID,
                qm.Marks,
                qm.BloomLevelID,
                qm.DifficultyLevelID,
                qm.IsEnable,
                qm.AddedDate,
                cm.CourseName,
                stm.StreamName,
                sm.SubjectName,
                tm.TopicName,
                qt.TypeName as QuestionTypeName,
                bl.LevelName as BloomLevelName,
                dl.LevelName as DifficultyLevelName,
                mcq.QuestionText,
                mcq.OptionA,
                mcq.OptionB,
                mcq.OptionC,
                mcq.OptionD,
                mcq.CorrectOption,
                mcq.ImgQuestion,
                qe.ExplanationText
            FROM QuestionMaster qm
            LEFT JOIN SubjectMaster sm ON qm.SubjectID = sm.SubjectID
            LEFT JOIN StreamMaster stm ON sm.StreamID = stm.StreamID
            LEFT JOIN CourseMaster cm ON stm.CourseID = cm.CourseID
            LEFT JOIN TopicMaster tm ON qm.TopicID = tm.TopicID
            LEFT JOIN QuestionType qt ON qm.QuestionTypeID = qt.QuestionTypeID
            LEFT JOIN BloomLevel bl ON qm.BloomLevelID = bl.BloomLevelID
            LEFT JOIN DifficultyLevel dl ON qm.DifficultyLevelID = dl.DifficultyLevelID
            LEFT JOIN MCQ_Questions mcq ON qm.QuestionID = mcq.QuestionID
            LEFT JOIN QuestionExplanation qe ON qm.QuestionID = qe.QuestionID
            WHERE qm.IsDeleted = 0
        """
        
        # Add status filter
        if status == 'approved':
            query += " AND qm.IsEnable = 1"
        elif status == 'discarded':
            query += " AND qm.IsDeleted = 1"
        elif status == 'pending':
            query += " AND qm.IsEnable = 0 AND qm.IsDeleted = 0"
        
        # Add additional filters
        params = []
        if course:
            query += " AND cm.CourseName = ?"
            params.append(course)
        if stream:
            query += " AND stm.StreamName = ?"
            params.append(stream)
        if subject:
            query += " AND sm.SubjectName = ?"
            params.append(subject)
        if topic:
            query += " AND tm.TopicName = ?"
            params.append(topic)
        if difficulty:
            query += " AND dl.LevelName = ?"
            params.append(difficulty)
        if bloom:
            query += " AND bl.LevelName = ?"
            params.append(bloom)
        
        query += " ORDER BY qm.AddedDate DESC"
        
        cursor.execute(query, params)
        
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        result = []
        for row in rows:
            result.append(dict(zip(columns, row)))
        
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Error getting questions: {e}")
        return []

def update_question_status(question_id, status):
    """Update question status (approve/discard)"""
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        if status == 'approved':
            cursor.execute("""
                UPDATE QuestionMaster 
                SET IsEnable = 1, IsPublic = 1, ApprovedDate = ?
                WHERE QuestionID = ?
            """, (datetime.now(), question_id))
        elif status == 'discarded':
            cursor.execute("""
                UPDATE QuestionMaster 
                SET IsDeleted = 1
                WHERE QuestionID = ?
            """, (question_id,))
        
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating question status: {e}")
        return False 

def get_courses():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT CourseID, CourseName FROM CourseMaster WHERE IsActive = 1")
        rows = cursor.fetchall()
        result = [{'CourseID': row[0], 'CourseName': row[1]} for row in rows]
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Error getting courses: {e}")
        return []

def get_streams_by_course(course_id):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT StreamID, StreamName FROM StreamMaster WHERE CourseID = ? AND IsActive = 1", (course_id,))
        rows = cursor.fetchall()
        result = [{'StreamID': row[0], 'StreamName': row[1]} for row in rows]
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Error getting streams: {e}")
        return []

def get_subjects_by_stream(stream_id):
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT SubjectID, SubjectName FROM SubjectMaster WHERE StreamID = ? AND IsActive = 1", (stream_id,))
        rows = cursor.fetchall()
        result = [{'SubjectID': row[0], 'SubjectName': row[1]} for row in rows]
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Error getting subjects by stream: {e}")
        return [] 