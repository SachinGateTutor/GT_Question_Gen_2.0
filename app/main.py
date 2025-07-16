import os
from flask import Flask, request, jsonify, send_from_directory, abort
from services.openai_service import generate_mcq_and_diagram
from services.diagram_service import render_diagram
from services.db_service import (
    get_subjects, get_topics_by_subject, get_reference_data,
    store_generated_question, get_questions_by_status, update_question_status,
    get_courses, get_streams_by_course, get_subjects_by_stream,
    add_course, update_course, delete_course, get_all_courses,
    add_stream, update_stream, delete_stream, get_all_streams,
    add_subject, update_subject, delete_subject, get_all_subjects,
    add_topic, update_topic, delete_topic, get_all_topics
)
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'images')

# Serve the main HTML file
@app.route('/')
def index():
    return send_from_directory('..', 'index.html')

# Serve static files (config.js, etc.)
@app.route('/<path:filename>')
def serve_static(filename):
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
    for i in range(num_questions):
        # Prepare data for OpenAI
        data_for_openai = data.copy()
        data_for_openai['subject'] = subject_for_prompt
        data_for_openai['topic'] = topic_for_prompt
    
        # Call OpenAI to get question and diagram code with library selection
        result = generate_mcq_and_diagram(data_for_openai)
    
        image_url = None
        option_images = []
        
        # Handle main question diagram
        if result.get('diagram_code'):
            library_used = result.get('library_used', 'schemdraw')
            image_filename = render_diagram(
                result['diagram_code'], 
                library_used, 
                app.config['UPLOAD_FOLDER']
            )
            if image_filename:
                image_url = f"/static/images/{image_filename}"
        
        # Handle option diagrams
        if result.get('option_diagram_codes'):
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
                        option_images.append(None)
                else:
                    option_images.append(None)
        
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
            db_data = {
                'subject_id': data.get('subject_id'),
                'topic_id': data.get('topic_id'),
                'question_type_id': data.get('question_type_id', 1),  # Default to MCQ
                'bloom_level_id': data.get('bloom_level_id'),
                'difficulty_level_id': data.get('difficulty_level_id'),
                'question_text': result.get('question_text'),
                'options': result.get('options', []),
                'correct_answer': result.get('correct_answer'),
                'explanation': result.get('explanation'),
                'diagram_image_url': image_url,
                'library_used': result.get('library_used', 'schemdraw'),
                'option_images': option_images
            }
            store_generated_question(db_data)
        
        all_questions.append(question_data)
    
    # Return the first question for backward compatibility, but also include all questions
    if all_questions:
        first_question = all_questions[0].copy()
        response = {
            'question_text': first_question.get('question_text'),
            'options': first_question.get('options'),
            'correct_answer': first_question.get('correct_answer'),
            'explanation': first_question.get('explanation'),
            'diagram_code': first_question.get('diagram_code'),
            'diagram_image_url': first_question.get('diagram_image_url'),
            'library_used': first_question.get('library_used', 'schemdraw'),
            'option_images': first_question.get('option_images'),
            'all_questions': all_questions,
            'total_generated': len(all_questions)
        }
    else:
        response = {
            'question_text': 'No questions generated',
            'options': [],
            'correct_answer': '',
            'explanation': '',
            'diagram_code': None,
            'diagram_image_url': None,
            'library_used': 'schemdraw',
            'option_images': None,
            'all_questions': [],
            'total_generated': 0
        }
    
    return jsonify(response)

# API endpoints for dropdown data
@app.route('/api/courses', methods=['GET'])
def get_courses_api():
    courses = get_courses()
    return jsonify(courses)

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
    
    questions = get_questions_by_status(status, course, stream, subject, topic, difficulty, bloom)
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

if __name__ == '__main__':
    # Get host and port from environment variables or use defaults
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print(f"🚀 Starting Flask server on {host}:{port}")
    print(f"📱 Access the application from other devices using your computer's IP address")
    print(f"🌐 Local access: http://localhost:{port}")
    print(f"📋 To find your IP address, run: ipconfig (Windows) or ifconfig (Mac/Linux)")
    
    app.run(host=host, port=port, debug=True) 