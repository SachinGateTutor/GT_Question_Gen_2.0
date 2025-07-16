import pyodbc
import os
from datetime import datetime
import json
import re

def get_db_connection():
    """Get SQL Server database connection"""
    try:

        # for local system

        conn = pyodbc.connect(
            'DRIVER={ODBC Driver 17 for SQL Server};'
            'SERVER=localhost;'
            'DATABASE=MCQGen;'
            'Trusted_Connection=yes;'
        )

        # for main system
        
        # conn = pyodbc.connect(
        #     'DRIVER={ODBC Driver 17 for SQL Server};'
        #     'SERVER=DESKTOP-2SUICFV;'
        #     'DATABASE=GTQuestionDB;'
        #     'Trusted_Connection=yes;'
        #     'UID=sa;'
        #     'PWD=Pass@123;'
        # )
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
    print(f"option_images: {data.get('option_images')}")
    options = data.get('options') or []
    
    # Clean the correct answer to extract just the letter (A, B, C, D)
    correct_answer = data.get('correct_answer', '')
    if correct_answer:
        # First try to extract just the letter from answers like "A. Option A" or "A"
        match = re.search(r'^([A-D])', correct_answer.strip())
        if match:
            correct_answer = match.group(1)
        else:
            # If no letter found, try to find the correct option by matching
            for i, option in enumerate(options):
                if option and option in correct_answer:
                    correct_answer = chr(65 + i)  # Convert to A, B, C, D
                    break
            else:
                # If still no match, try to extract any letter from the answer
                letter_match = re.search(r'([A-D])', correct_answer.upper())
                if letter_match:
                    correct_answer = letter_match.group(1)
                else:
                    correct_answer = 'A'  # Default fallback
    else:
        correct_answer = 'A'  # Default if no correct answer provided
    
    # Ensure correct_answer is always A, B, C, or D
    if correct_answer not in ['A', 'B', 'C', 'D']:
        correct_answer = 'A'
    
    print(f"🔍 Debug: Final correct_answer: {correct_answer}")
    
    # Get option images
    option_images = data.get('option_images') or []
    img_option_a = option_images[0] if len(option_images) > 0 else None
    img_option_b = option_images[1] if len(option_images) > 1 else None
    img_option_c = option_images[2] if len(option_images) > 2 else None
    img_option_d = option_images[3] if len(option_images) > 3 else None
    
    print(f"🔍 Debug: Option images - A: {img_option_a}, B: {img_option_b}, C: {img_option_c}, D: {img_option_d}")
    
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO MCQ_Questions 
            (QuestionID, QuestionText, OptionA, OptionB, OptionC, OptionD, 
             CorrectOption, HasImage, ImgQuestion, ImgOptionA, ImgOptionB, ImgOptionC, ImgOptionD)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            question_id,
            data.get('question_text'),
            options[0] if len(options) > 0 else None,
            options[1] if len(options) > 1 else None,
            options[2] if len(options) > 2 else None,
            options[3] if len(options) > 3 else None,
            correct_answer,
            1 if data.get('diagram_image_url') or any([img_option_a, img_option_b, img_option_c, img_option_d]) else 0,
            data.get('diagram_image_url'),
            img_option_a,
            img_option_b,
            img_option_c,
            img_option_d
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
                mcq.ImgOptionA,
                mcq.ImgOptionB,
                mcq.ImgOptionC,
                mcq.ImgOptionD,
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

def add_course(course_name):
    """Add a new course"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO CourseMaster (CourseName, IsActive)
            VALUES (?, 1)
        """, (course_name,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding course: {e}")
        return False

def update_course(course_id, course_name):
    """Update an existing course"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE CourseMaster 
            SET CourseName = ?
            WHERE CourseID = ?
        """, (course_name, course_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating course: {e}")
        return False

def delete_course(course_id):
    """Soft delete a course"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE CourseMaster 
            SET IsActive = 0
            WHERE CourseID = ?
        """, (course_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting course: {e}")
        return False

def get_all_courses():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT CourseID, CourseName, IsActive FROM CourseMaster ORDER BY CourseName")
        rows = cursor.fetchall()
        result = [{'CourseID': row[0], 'CourseName': row[1], 'IsActive': row[2]} for row in rows]
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Error getting all courses: {e}")
        return []

def add_stream(course_id, stream_name):
    """Add a new stream"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO StreamMaster (CourseID, StreamName, IsActive)
            VALUES (?, ?, 1)
        """, (course_id, stream_name))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding stream: {e}")
        return False

def update_stream(stream_id, stream_name):
    """Update an existing stream"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE StreamMaster 
            SET StreamName = ?
            WHERE StreamID = ?
        """, (stream_name, stream_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating stream: {e}")
        return False

def delete_stream(stream_id):
    """Soft delete a stream"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE StreamMaster 
            SET IsActive = 0
            WHERE StreamID = ?
        """, (stream_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting stream: {e}")
        return False

def get_all_streams():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT StreamID, StreamName, CourseID, IsActive FROM StreamMaster ORDER BY StreamName")
        rows = cursor.fetchall()
        result = [{'StreamID': row[0], 'StreamName': row[1], 'CourseID': row[2], 'IsActive': row[3]} for row in rows]
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Error getting all streams: {e}")
        return []

def add_subject(stream_id, subject_name):
    """Add a new subject"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO SubjectMaster (StreamID, SubjectName, IsActive)
            VALUES (?, ?, 1)
        """, (stream_id, subject_name))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding subject: {e}")
        return False

def update_subject(subject_id, subject_name):
    """Update an existing subject"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE SubjectMaster 
            SET SubjectName = ?
            WHERE SubjectID = ?
        """, (subject_name, subject_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating subject: {e}")
        return False

def delete_subject(subject_id):
    """Soft delete a subject"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE SubjectMaster 
            SET IsActive = 0
            WHERE SubjectID = ?
        """, (subject_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting subject: {e}")
        return False

def get_all_subjects():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT SubjectID, SubjectName, StreamID, IsActive FROM SubjectMaster ORDER BY SubjectName")
        rows = cursor.fetchall()
        result = [{'SubjectID': row[0], 'SubjectName': row[1], 'StreamID': row[2], 'IsActive': row[3]} for row in rows]
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Error getting all subjects: {e}")
        return []

def add_topic(subject_id, topic_name, bloom_level_id=1):
    """Add a new topic"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO TopicMaster (SubjectID, TopicName, BloomLevelID, IsActive)
            VALUES (?, ?, ?, 1)
        """, (subject_id, topic_name, bloom_level_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error adding topic: {e}")
        return False

def update_topic(topic_id, topic_name, bloom_level_id=1):
    """Update an existing topic"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE TopicMaster 
            SET TopicName = ?, BloomLevelID = ?
            WHERE TopicID = ?
        """, (topic_name, bloom_level_id, topic_id))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error updating topic: {e}")
        return False

def delete_topic(topic_id):
    """Soft delete a topic"""
    conn = get_db_connection()
    if not conn:
        return False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE TopicMaster 
            SET IsActive = 0
            WHERE TopicID = ?
        """, (topic_id,))
        conn.commit()
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting topic: {e}")
        return False

def get_all_topics():
    conn = get_db_connection()
    if not conn:
        return []
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT TopicID, TopicName, SubjectID, BloomLevelID, IsActive FROM TopicMaster ORDER BY TopicName")
        rows = cursor.fetchall()
        result = [{'TopicID': row[0], 'TopicName': row[1], 'SubjectID': row[2], 'BloomLevelID': row[3], 'IsActive': row[4]} for row in rows]
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"Error getting all topics: {e}")
        return [] 