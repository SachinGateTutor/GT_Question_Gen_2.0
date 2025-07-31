import os
import threading
import uuid
import shutil
import time
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory, abort
from services.openai_service import generate_mcq_and_diagram, ai_analyze_topic, generate_replacement_question
from services.diagram_service_new import render_diagram
from services.bloom_detector import detect_bloom_level, update_question_bloom_level

from services.db_service import (
    get_subjects, get_topics_by_subject, get_reference_data,
    store_generated_question, get_questions_by_status, update_question_status,
    get_courses, get_streams_by_course, get_subjects_by_stream,
    add_course, update_course, delete_course, get_all_courses,
    add_stream, update_stream, delete_stream, get_all_streams,
    add_subject, update_subject, delete_subject, get_all_subjects,
    add_topic, update_topic, delete_topic, get_all_topics, get_topic_details
)
from services.ai_explanation_service import ai_explanation_service
from flask_cors import CORS
import traceback

# Global storage for active generations
active_generations = {}

# Image monitoring variables
image_monitor_running = False
image_monitor_thread = None

# Removed fallback diagram generation - let it be None when diagram generation fails

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'images')

def start_image_monitoring():
    """Start image monitoring in background thread"""
    global image_monitor_running, image_monitor_thread
    
    if image_monitor_running:
        return
    
    def monitor_images():
        global image_monitor_running
        # Get the project root directory (one level up from app directory)
        project_root = Path(__file__).parent.parent
        images_dir = project_root / "app" / "static" / "images"
        
        # Ensure images directory exists
        images_dir.mkdir(parents=True, exist_ok=True)
        
        print("🚀 Starting integrated image monitoring...")
        print(f"📁 Monitoring: {project_root}")
        print(f"📁 Destination: {images_dir}")
        
        image_monitor_running = True
        
        while image_monitor_running:
            try:
                # Find PNG files in project root directory (excluding app/static/images)
                png_files = []
                for file_path in project_root.rglob("*.png"):
                    if file_path.is_file() and not str(file_path).startswith(str(images_dir)):
                        # Skip if file is already in the images directory
                        if file_path.parent == images_dir:
                            continue
                        png_files.append(file_path)
                
                # Move files
                for source_path in png_files:
                    filename = source_path.name
                    dest_path = images_dir / filename
                    
                    try:
                        # Skip if file is already in destination
                        if source_path.parent == images_dir:
                            continue
                            
                        # Check if destination file exists
                        if dest_path.exists():
                            # Replace the existing file
                            dest_path.unlink()
                            print(f"🔄 Replaced existing: {filename}")
                        else:
                            print(f"📁 New file: {filename}")
                        
                        # Move the file
                        shutil.move(str(source_path), str(dest_path))
                        print(f"✅ Moved: {filename} -> static/images/")
                        
                    except Exception as e:
                        print(f"❌ Error moving {filename}: {e}")
                
                # Sleep before next check
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Image monitoring error: {e}")
                time.sleep(5)
    
    # Start monitoring thread
    image_monitor_thread = threading.Thread(target=monitor_images, daemon=True)
    image_monitor_thread.start()
    print("✅ Image monitoring started successfully")

def stop_image_monitoring():
    """Stop image monitoring"""
    global image_monitor_running
    image_monitor_running = False
    print("🛑 Image monitoring stopped")

# Start image monitoring when app starts
def initialize_app():
    """Initialize the application and start image monitoring"""
    try:
        start_image_monitoring()
    except Exception as e:
        print(f"⚠️  Could not start image monitoring: {e}")

# Initialize app when Flask starts
with app.app_context():
    initialize_app()

# Serve the main HTML file
@app.route('/')
def index():
    return send_from_directory('..', 'index.html')

# Serve static files (config.js, etc.)
@app.route('/<path:filename>')
def serve_static(filename):
    # Check if it's an image file in static/images
    if filename.startswith('static/images/'):
        # Serve from app directory (images are in app/static/images/)
        return send_from_directory('.', filename)
    else:
        # Serve other static files from root directory
        return send_from_directory('..', filename)

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    num_questions = data.get('num_questions', 1)
    
    # Look up subject and topic names from IDs
    subject_id = data.get('subject_id')
    topic_id = data.get('topic_id')
    subject_name = None
    topic_name = None
    if subject_id:
        subjects = get_subjects()
        for subj in subjects:
            if subj['SubjectID'] == subject_id:
                subject_name = subj['SubjectName']
                break
    if topic_id:
        topics = get_topics_by_subject(subject_id)
        for top in topics:
            if top['TopicID'] == topic_id:
                topic_name = top['TopicName']
                break
    # Fallback to IDs if names not found
    subject_for_prompt = subject_name if subject_name else subject_id
    topic_for_prompt = topic_name if topic_name else topic_id
    
    # Generate multiple questions
    all_questions = []
    question_id = None  # Ensure question_id is always defined
    try:
        for i in range(num_questions):
            # Prepare data for OpenAI
            data_for_openai = data.copy()
            data_for_openai['subject'] = subject_for_prompt
            data_for_openai['topic'] = topic_for_prompt
        
            # Call OpenAI to get question and diagram code with library selection
            result = generate_mcq_and_diagram(data_for_openai)
        
            image_url = None
            option_images = []
            
            # Handle main question diagram with self-healing system
            if result.get('diagram_code'):
                library_used = result.get('library_used', 'schemdraw')
                image_filename = render_diagram(
                    result['diagram_code'], 
                    library_used, 
                    app.config['UPLOAD_FOLDER']
                )
                
                # Self-healing: If diagram generation failed, try replacement question
                if image_filename:
                    image_url = f"/static/images/{image_filename}"
                    print(f"✅ Diagram generated successfully: {image_filename}")
                else:
                    print(f"❌ Diagram generation failed completely for {library_used}")
                    print(f"🔄 Attempting to generate replacement question...")
                    
                    # Generate replacement question if diagram was required
                    if data.get('requires_diagram', False):
                        try:
                            replacement_data = generate_replacement_question(
                                subject=subject_for_prompt,
                                topic=topic_for_prompt,
                                difficulty_level=data.get('difficulty_level', 'Medium'),
                                bloom_level=data.get('bloom_level_id', 3),
                                requires_diagram=True,
                                library_name=library_used
                            )
                            
                            if replacement_data:
                                print(f"✅ Generated replacement question successfully")
                                # Update result with replacement data
                                result.update(replacement_data)
                                
                                # Try to generate diagram for replacement question
                                if replacement_data.get('diagram_code'):
                                    replacement_image_filename = render_diagram(
                                        replacement_data['diagram_code'],
                                        library_used,
                                        app.config['UPLOAD_FOLDER']
                                    )
                                    if replacement_image_filename:
                                        image_url = f"/static/images/{replacement_image_filename}"
                                        print(f"✅ Replacement question diagram generated: {replacement_image_filename}")
                                    else:
                                        print(f"❌ Replacement question diagram also failed, proceeding without diagram")
                                        print(f"📝 Note: No misleading diagram will be shown - better for educational accuracy")
                                        image_url = None
                                else:
                                    print(f"❌ Replacement question has no diagram code")
                                    image_url = None
                            else:
                                print(f"❌ Failed to generate replacement question, proceeding with original")
                                image_url = None
                        except Exception as replacement_error:
                            print(f"❌ Replacement question generation failed: {replacement_error}")
                            image_url = None
                    else:
                        print(f"⚠️ Diagram not required, proceeding without diagram")
                        image_url = None
            
            # Handle option diagrams - only if user requested them
            requires_option_diagrams = data.get('requires_option_diagrams', False)
            if requires_option_diagrams and result.get('option_diagram_codes'):
                library_used = result.get('library_used', 'schemdraw')
                option_diagram_codes = result.get('option_diagram_codes', {})
                
                for option in ['A', 'B', 'C', 'D']:
                    option_code = option_diagram_codes.get(option)
                    if option_code:
                        option_image_filename = render_diagram(
                            option_code,
                            library_used,
                            app.config['UPLOAD_FOLDER']
                        )
                        if option_image_filename:
                            option_images.append(f"/static/images/{option_image_filename}")
                        else:
                            # Fallback: generate a default diagram
                            print(f"⚠️ Debug: Failed to render option {option} diagram, generating fallback")
                            # Fallback: generate a default diagram
                            option_images.append(None)
                    else:
                        # Generate fallback diagram for missing option
                        print(f"⚠️ Debug: No code for option {option}, generating fallback")
                        option_images.append(None)
            else:
                # If option diagrams are not requested, set all to None
                option_images = [None, None, None, None]
            
            question_data = {
                'question_text': result.get('question_text'),
                'options': result.get('options'),
                'correct_answer': result.get('correct_answer'),
                'explanation': result.get('explanation'),
                'diagram_code': result.get('diagram_code'),
                'diagram_image_url': image_url,
                'library_used': result.get('library_used', 'schemdraw'),
                'option_images': option_images if option_images else None
            }
            
            # Store the generated question in database
            if result.get('question_text'):
                # Handle Bloom level detection if 'auto_detect' is selected
                bloom_level = data.get('bloom_level')
                detected_bloom_level = None
                
                if bloom_level == 'auto_detect':
                    print("🔍 Auto-detecting Bloom level for question...")
                    detected_bloom_level = detect_bloom_level(
                        result.get('question_text'),
                        result.get('options', []),
                        result.get('explanation', '')
                    )
                    if detected_bloom_level:
                        bloom_level_id = detected_bloom_level
                        print(f"✅ Bloom level auto-detected: {detected_bloom_level}")
                    else:
                        bloom_level_id = None  # Default to None if detection fails
                        print("⚠️ Bloom level detection failed, using None")
                else:
                    # Convert bloom level name to ID
                    bloom_level_id = None
                    if bloom_level:
                        # Get bloom level ID from name
                        bloom_levels = get_reference_data('BloomLevel')
                        for level in bloom_levels:
                            if level.get('LevelName') == bloom_level:
                                bloom_level_id = level.get('BloomLevelID')
                                break
                
                db_data = {
                    'subject_id': data.get('subject_id'),
                    'topic_id': data.get('topic_id'),
                    'question_type_id': data.get('question_type_id', 1),  # Default to MCQ
                    'bloom_level_id': bloom_level_id,
                    'difficulty_level_id': data.get('difficulty_level_id'),
                    'question_text': result.get('question_text'),
                    'options': result.get('options', []),
                    'correct_answer': result.get('correct_answer'),
                    'explanation': result.get('explanation'),
                    'diagram_image_url': image_url,
                    'library_used': result.get('library_used', 'schemdraw'),
                    'option_images': option_images,
                    'diagram_code': result.get('diagram_code')  # Add diagram code
                }
                
                # Store the generated question in database
                question_id = store_generated_question(db_data)
                
                # If Bloom level was auto-detected, update the question with the detected level
                if data.get('bloom_level') == 'auto_detect' and detected_bloom_level and question_id:
                    update_question_bloom_level(question_id, detected_bloom_level)
            
            all_questions.append(question_data)
        
        # Return the first question for backward compatibility, but also include all questions
        if all_questions:
            first_question = all_questions[0].copy()
            response = {
                'question_id': question_id,  # Add question ID to response
                'question_text': first_question.get('question_text'),
                'options': first_question.get('options'),
                'correct_answer': first_question.get('correct_answer'),
                'explanation': first_question.get('explanation'),
                'diagram_code': first_question.get('diagram_code'),
                'diagram_image_url': first_question.get('diagram_image_url'),
                'library_used': first_question.get('library_used', 'schemdraw'),
                'option_images': first_question.get('option_images'),
                'bloom_level': detected_bloom_level if detected_bloom_level else bloom_level_id,
                'all_questions': all_questions,
                'total_generated': len(all_questions)
            }
        else:
            response = {
                'question_id': None,
                'question_text': 'No questions generated',
                'options': [],
                'correct_answer': '',
                'explanation': '',
                'diagram_code': None,
                'diagram_image_url': None,
                'library_used': 'schemdraw',
                'option_images': None,
                'bloom_level': None,
                'all_questions': [],
                'total_generated': 0
            }
    
    except Exception as e:
        print(f"❌ Error in generate endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e),
            'question_id': question_id if 'question_id' in locals() else None,
            'library_used': None,
            'diagram_image_url': None,
            'question_text': None,
            'options': [],
            'correct_answer': None,
            'explanation': None,
            'bloom_level': None
        }), 500
    
    return jsonify(response)

# CDQ API Endpoint
@app.route('/api/generate_cdq', methods=['POST'])
def generate_cdq():
    """Generate CDQ (Context Dependent Question) with diagram"""
    try:
        data = request.get_json()
        
        # Extract required parameters
        topic_id = data.get('topic_id')
        subject_id = data.get('subject_id')
        stream_id = data.get('stream_id')
        course_id = data.get('course_id')
        context_type = data.get('context_type', 'real_world')
        difficulty_level_id = data.get('difficulty_level_id', 2)
        bloom_level_id = data.get('bloom_level_id', 2)
        requires_diagram = data.get('requires_diagram', False)  # Get user's diagram preference
        
        if not all([topic_id, subject_id, stream_id, course_id]):
            return jsonify({
                'error': 'Missing required parameters: topic_id, subject_id, stream_id, course_id'
            }), 400
        
        # Prepare data for CDQ generation
        question_data = {
            'course_id': course_id,
            'stream_id': stream_id,
            'subject_id': subject_id,
            'topic_id': topic_id,
            'question_type_id': 6,  # CDQ (ID 6 from database)
            'difficulty_level_id': difficulty_level_id,
            'bloom_level_id': bloom_level_id,
            'question_type': 'CDQ',
            'requires_diagram': requires_diagram,  # Use user's diagram preference
            'requires_option_diagrams': False,
            'is_programming_question': False,
            'custom_prompt': f"Generate a CDQ with {context_type} context. Focus on practical application and real-world scenarios.",
            'num_questions': 4  # Generate 4 questions for CDQ passage
        }
        
        # Generate CDQ with passage and questions
        from services.openai_service import generate_cdq_complete
        result = generate_cdq_complete(question_data)
        
        if result and result.get('passage_text') and result.get('questions'):
            # Store passage first
            from services.db_service import insert_cdq_passage
            passage_data = {
                'subject_id': subject_id,
                'topic_id': topic_id,
                'passage_text': result['passage_text']
            }
            print(f"🔍 Debug: Storing CDQ passage with data: {passage_data}")
            passage_id = insert_cdq_passage(passage_data)
            print(f"🔍 Debug: CDQ passage stored with ID: {passage_id}")
            
            if passage_id:
                # Store each question with passage reference
                stored_questions = []
                for i, question in enumerate(result['questions']):
                    # Create question master entry
                    question_master_data = {
                        'subject_id': subject_id,
                        'topic_id': topic_id,
                        'question_type_id': 6,  # CDQ (ID 6 from database)
                        'bloom_level_id': bloom_level_id,
                        'difficulty_level_id': difficulty_level_id,
                        'marks': 1
                    }
                    
                    # Store question master
                    from services.db_service import insert_question_master
                    question_id = insert_question_master(question_master_data)
                    
                    if question_id:
                        # Store CDQ question with passage reference
                        from services.db_service import insert_cdq_question
                        cdq_success = insert_cdq_question(passage_id, question_id)
                        
                        if cdq_success:
                            # Store MCQ question details
                            mcq_data = {
                                'question_id': question_id,
                                'question_text': question.get('question_text', ''),
                                'options': question.get('options', []),
                                'correct_answer': question.get('correct_answer', ''),
                                'diagram_code': question.get('diagram_code') if requires_diagram else None,
                                'diagram_image_url': question.get('diagram_image_url') if requires_diagram else None
                            }
                            
                            # Add auto-detected Bloom level if available
                            if result.get('detected_bloom_level_id'):
                                mcq_data['detected_bloom_level_id'] = result['detected_bloom_level_id']
                            
                            from services.db_service import insert_mcq_question
                            mcq_success = insert_mcq_question(question_id, mcq_data)
                            
                            if mcq_success:
                                # Store explanation if available
                                if question.get('explanation'):
                                    explanation_data = {
                                        'question_id': question_id,
                                        'explanation_text': question.get('explanation', '')
                                    }
                                    from services.db_service import insert_question_explanation
                                    insert_question_explanation(question_id, explanation_data)
                                
                                stored_questions.append(question_id)
            
                # Check if we have stored questions and return appropriate response
                if stored_questions:
                    print(f"🔍 Debug: CDQ generation successful - Passage ID: {passage_id}, Question IDs: {stored_questions}")
                return jsonify({
                    'success': True,
                        'passage_id': passage_id,
                        'question_ids': stored_questions,
                        'passage_text': result['passage_text'],
                        'questions': result['questions'],  # Add the questions array
                        'total_questions': len(stored_questions),
                    'context_type': context_type
                })
            else:
                return jsonify({
                        'error': 'Failed to store CDQ questions'
                }), 500
        else:
            return jsonify({
                'error': 'Failed to generate CDQ',
                'message': 'No passage or questions generated'
            }), 500
            
    except Exception as e:
        print(f"Error in generate_cdq: {e}")
        return jsonify({
            'error': 'Failed to generate CDQ',
            'message': str(e)
        }), 500

# API endpoints for dropdown data
@app.route('/api/courses', methods=['GET'])
def get_courses_api():
    """Get all courses"""
    try:
        courses = get_courses()
        return jsonify(courses)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/streams/<int:course_id>', methods=['GET'])
def get_streams_api(course_id):
    streams = get_streams_by_course(course_id)
    return jsonify(streams)

@app.route('/api/subjects', methods=['GET'])
def get_subjects_api():
    stream_id = request.args.get('stream_id')
    if stream_id:
        subjects = get_subjects_by_stream(int(stream_id))
    else:
        subjects = get_subjects()
    return jsonify(subjects)

@app.route('/api/topics/<int:subject_id>', methods=['GET'])
def get_topics_api(subject_id):
    """Get topics for a specific subject"""
    topics = get_topics_by_subject(subject_id)
    return jsonify(topics)

@app.route('/api/reference/<table_name>', methods=['GET'])
def get_reference_api(table_name):
    """Get reference data for dropdowns (QuestionType, BloomLevel, DifficultyLevel, etc.)"""
    allowed_tables = ['QuestionType', 'BloomLevel', 'DifficultyLevel', 'SectionType']
    if table_name not in allowed_tables:
        return jsonify({'error': 'Invalid table name'}), 400
    
    data = get_reference_data(table_name)
    return jsonify(data)

# API endpoints for question management
@app.route('/api/questions', methods=['GET'])
def get_questions_api():
    """Get all questions with optional filters"""
    status = request.args.get('status', 'all')
    course = request.args.get('course', '')
    stream = request.args.get('stream', '')
    subject = request.args.get('subject', '')
    topic = request.args.get('topic', '')
    difficulty = request.args.get('difficulty', '')
    bloom = request.args.get('bloom', '')
    question_type = request.args.get('questionType', '')
    
    questions = get_questions_by_status(status, course, stream, subject, topic, difficulty, bloom, question_type)
    return jsonify(questions)

@app.route('/api/questions/<int:question_id>/status', methods=['POST'])
def update_question_status_api(question_id):
    """Update question status (approve/discard)"""
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['approved', 'discarded']:
        return jsonify({'error': 'Invalid status'}), 400
    
    success = update_question_status(question_id, status)
    return jsonify({'success': success})

@app.route('/api/explain-question', methods=['POST'])
def explain_question_api():
    """Generate AI explanation for a question"""
    try:
        data = request.get_json()
        
        # Extract question data
        question_data = {
            'question_id': data.get('question_id'),
            'question_text': data.get('question_text', ''),
            'options': data.get('options', []),
            'correct_answer': data.get('correct_answer', ''),
            'topic': data.get('topic', ''),
            'subject': data.get('subject', ''),
            'difficulty_level': data.get('difficulty_level', 'Medium'),
            'question_type': data.get('question_type', 'MCQ'),
            'bloom_level': data.get('bloom_level', 'Understand')
        }
        
        # Validate required fields
        if not question_data['question_text']:
            return jsonify({'error': 'Question text is required'}), 400
        
        # Generate AI explanation
        explanation = ai_explanation_service.generate_question_explanation(question_data)
        
        return jsonify(explanation)
        
    except Exception as e:
        print(f"Error in explain_question_api: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to generate explanation',
            'message': str(e)
        }), 500

# --- Admin API Endpoints ---
# Course
@app.route('/api/admin/courses', methods=['GET', 'POST'])
def admin_courses():
    if request.method == 'GET':
        return jsonify(get_all_courses())
    elif request.method == 'POST':
        data = request.get_json()
        success = add_course(data['CourseName'])
        return jsonify({'success': success, 'message': 'Course added successfully' if success else 'Failed to add course'})
    return abort(405)

@app.route('/api/admin/courses/<int:course_id>', methods=['PUT', 'DELETE'])
def admin_course_modify(course_id):
    data = request.get_json()
    if request.method == 'PUT':
        success = update_course(course_id, data['CourseName'])
        return jsonify({'success': success, 'message': 'Course updated successfully' if success else 'Failed to update course'})
    elif request.method == 'DELETE':
        success = delete_course(course_id)
        return jsonify({'success': success, 'message': 'Course deleted successfully' if success else 'Failed to delete course'})
    return abort(405)

# Stream
@app.route('/api/admin/streams', methods=['GET', 'POST'])
def admin_streams():
    if request.method == 'GET':
        return jsonify(get_all_streams())
    elif request.method == 'POST':
        data = request.get_json()
        success = add_stream(data['CourseID'], data['StreamName'])
        return jsonify({'success': success, 'message': 'Stream added successfully' if success else 'Failed to add stream'})
    return abort(405)

@app.route('/api/admin/streams/<int:stream_id>', methods=['PUT', 'DELETE'])
def admin_stream_modify(stream_id):
    data = request.get_json()
    if request.method == 'PUT':
        success = update_stream(stream_id, data['StreamName'])
        return jsonify({'success': success, 'message': 'Stream updated successfully' if success else 'Failed to update stream'})
    elif request.method == 'DELETE':
        success = delete_stream(stream_id)
        return jsonify({'success': success, 'message': 'Stream deleted successfully' if success else 'Failed to delete stream'})
    return abort(405)

# Subject
@app.route('/api/admin/subjects', methods=['GET', 'POST'])
def admin_subjects():
    if request.method == 'GET':
        return jsonify(get_all_subjects())
    elif request.method == 'POST':
        data = request.get_json()
        success = add_subject(data['StreamID'], data['SubjectName'])
        return jsonify({'success': success, 'message': 'Subject added successfully' if success else 'Failed to add subject'})
    return abort(405)

@app.route('/api/admin/subjects/<int:subject_id>', methods=['PUT', 'DELETE'])
def admin_subject_modify(subject_id):
    data = request.get_json()
    if request.method == 'PUT':
        success = update_subject(subject_id, data['SubjectName'])
        return jsonify({'success': success, 'message': 'Subject updated successfully' if success else 'Failed to update subject'})
    elif request.method == 'DELETE':
        success = delete_subject(subject_id)
        return jsonify({'success': success, 'message': 'Subject deleted successfully' if success else 'Failed to delete subject'})
    return abort(405)

# Topic
@app.route('/api/admin/topics', methods=['GET', 'POST'])
def admin_topics():
    if request.method == 'GET':
        return jsonify(get_all_topics())
    elif request.method == 'POST':
        data = request.get_json()
        bloom_level_id = data.get('BloomLevelID', 1)
        success = add_topic(data['SubjectID'], data['TopicName'], bloom_level_id)
        return jsonify({'success': success, 'message': 'Topic added successfully' if success else 'Failed to add topic'})
    return abort(405)

@app.route('/api/admin/topics/<int:topic_id>', methods=['PUT', 'DELETE'])
def admin_topic_modify(topic_id):
    data = request.get_json()
    if request.method == 'PUT':
        bloom_level_id = data.get('BloomLevelID', 1)
        success = update_topic(topic_id, data['TopicName'], bloom_level_id)
        return jsonify({'success': success, 'message': 'Topic updated successfully' if success else 'Failed to update topic'})
    elif request.method == 'DELETE':
        success = delete_topic(topic_id)
        return jsonify({'success': success, 'message': 'Topic deleted successfully' if success else 'Failed to delete topic'})
    return abort(405)

# Random Question Generation Endpoints
@app.route('/api/analyze-topic', methods=['POST'])
def analyze_topic():
    """Analyze topic and return AI recommendations for question generation"""
    try:
        data = request.json
        course_id = data.get('course_id')
        stream_id = data.get('stream_id') 
        subject_id = data.get('subject_id')
        topic_id = data.get('topic_id')
        question_type = data.get('question_type')
        
        # Get topic details from database
        topic_info = get_topic_details(topic_id, subject_id, stream_id, course_id)
        if not topic_info:
            return jsonify({
                'success': False,
                'error': 'Topic information not found'
            }), 404
        
        # Call AI analysis service
        analysis_result = ai_analyze_topic(topic_info, question_type)
        
        return jsonify({
            'success': True,
            'analysis': analysis_result,
            'topic_info': topic_info
        })
        
    except Exception as e:
        print(f"Topic analysis error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'AI analysis failed. Please switch to manual input.'
        }), 500

@app.route('/api/generate-random', methods=['POST'])
def generate_random_questions():
    """Generate questions based on AI analysis with real-time progress"""
    try:
        data = request.json
        question_plan = data.get('question_plan')
        generation_id = str(uuid.uuid4())
        
        # Store generation session
        active_generations[generation_id] = {
            'status': 'active',
            'progress': {
                'current': 0,
                'total': question_plan['total_questions'],
                'diagram_current': 0,
                'diagram_total': question_plan['diagram_questions'],
                'option_diagram_current': 0,
                'option_diagram_total': question_plan['option_diagram_questions'],
                'text_only_current': 0,
                'text_only_total': question_plan['text_only_questions'],
                'code_current': 0,
                'code_total': question_plan['code_questions']
            },
            'generated_questions': [],
            'start_time': datetime.now()
        }
        
        # Start background generation
        thread = threading.Thread(
            target=generate_questions_background,
            args=(generation_id, data, question_plan)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'generation_id': generation_id
        })
        
    except Exception as e:
        print(f"Random generation error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generation-progress/<generation_id>')
def get_generation_progress(generation_id):
    """Get real-time progress of question generation"""
    if generation_id in active_generations:
        session = active_generations[generation_id]
        return jsonify({
            'success': True,
            'progress': session['progress'],
            'status': session['status'],
            'generated_questions': session.get('generated_questions', [])  # Include generated questions
        })
    else:
        return jsonify({'success': False, 'error': 'Generation not found'}), 404

@app.route('/api/stop-generation/<generation_id>', methods=['POST'])
def stop_generation(generation_id):
    """Stop ongoing question generation"""
    if generation_id in active_generations:
        active_generations[generation_id]['status'] = 'stopped'
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Generation not found'}), 404

def generate_questions_background(generation_id, request_data, question_plan):
    """Background function to generate questions with progress updates"""
    try:
        session = active_generations[generation_id]
        progress = session['progress']
        
        # Generate each type of question
        question_types = [
            ('diagram', question_plan['diagram_questions']),
            ('option_diagram', question_plan['option_diagram_questions']),
            ('text_only', question_plan['text_only_questions']),
            ('code', question_plan['code_questions'])
        ]
        
        for q_type, count in question_types:
            for i in range(count):
                # Check if generation was stopped
                if session['status'] == 'stopped':
                    break
                    
                # Generate individual question
                question_data = generate_single_question(request_data, q_type)
                
                if question_data:
                    # Store in database
                    question_id = store_generated_question(question_data)
                    
                    # Update progress
                    progress['current'] += 1
                    progress[f'{q_type}_current'] += 1
                    
                    session['generated_questions'].append({
                        'id': question_id,
                        'type': q_type,
                        'question': question_data
                    })
                
            if session['status'] == 'stopped':
                break
        
        # Mark as completed
        if session['status'] != 'stopped':
            session['status'] = 'completed'
            
    except Exception as e:
        print(f"Background generation error: {str(e)}")
        session['status'] = 'error'
        session['error'] = str(e)

def generate_single_question(request_data, question_type):
    """Generate a single question based on type"""
    enhanced_request = request_data.copy()
    
    # Modify request based on question type
    if question_type == 'diagram':
        enhanced_request['requires_diagram'] = True
        enhanced_request['requires_option_diagrams'] = False
    elif question_type == 'option_diagram':
        enhanced_request['requires_diagram'] = False
        enhanced_request['requires_option_diagrams'] = True
    elif question_type == 'code':
        enhanced_request['is_programming_question'] = True
    else:  # text_only
        enhanced_request['requires_diagram'] = False
        enhanced_request['requires_option_diagrams'] = False
        enhanced_request['is_programming_question'] = False
    
    # Call existing generation function
    generated_data = generate_mcq_and_diagram(enhanced_request)
    
    # Merge generated data with original request data for database storage
    if generated_data and 'error' not in generated_data:
        # Add database fields from original request
        generated_data.update({
            'subject_id': request_data.get('subject_id'),
            'topic_id': request_data.get('topic_id'),
            'question_type_id': 1,  # MCQ
            'bloom_level_id': request_data.get('bloom_level_id', 1),
            'difficulty_level_id': request_data.get('difficulty_level_id', 1),
            'marks': 1
        })
        
        # Handle diagram rendering if needed
        if generated_data.get('diagram_code'):
            try:
                from services.renderers.random_generation_renderer import render_diagram_for_random
                import os
                # Set the output folder for diagram images
                output_folder = app.config['UPLOAD_FOLDER']
                diagram_result = render_diagram_for_random(generated_data['diagram_code'], generated_data['library_used'], output_folder)
                if diagram_result and diagram_result.get('success') and diagram_result.get('image_url'):
                    generated_data['diagram_image_url'] = diagram_result['image_url']
                else:
                    generated_data['diagram_image_url'] = None
            except Exception as e:
                print(f"Diagram rendering error: {e}")
                generated_data['diagram_image_url'] = None
        
        # Handle option diagrams if needed
        if generated_data.get('option_diagram_codes'):
            option_images = []
            for option, code in generated_data['option_diagram_codes'].items():
                if code:
                    try:
                        from services.renderers.random_generation_renderer import render_option_diagram_for_random
                        import os
                        # Set the output folder for diagram images
                        output_folder = app.config['UPLOAD_FOLDER']
                        diagram_result = render_option_diagram_for_random(code, generated_data['library_used'], output_folder)
                        if diagram_result and diagram_result.get('success') and diagram_result.get('image_url'):
                            option_images.append(diagram_result['image_url'])
                        else:
                            option_images.append(None)
                    except Exception as e:
                        print(f"Option diagram rendering error: {e}")
                        option_images.append(None)
                else:
                    option_images.append(None)
            generated_data['option_images'] = option_images
    
    return generated_data

if __name__ == '__main__':
    # Get host and port from environment variables or use defaults
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print(f"🚀 Starting Flask server on {host}:{port}")
    print(f"📱 Access the application from other devices using your computer's IP address")
    # print(f"🌐 Local access: http://localhost:{port}")
    print(f"📋 To find your IP address, run: ipconfig (Windows) or ifconfig (Mac/Linux)")
    
    # Disable watchdog to prevent restarts during question generation
    app.run(host=host, port=port, debug=True, use_reloader=False) 