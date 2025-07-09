import os
from flask import Flask, request, jsonify, send_from_directory
from services.openai_service import generate_mcq_and_diagram
from services.diagram_service import render_diagram
from services.db_service import (
    get_subjects, get_topics_by_subject, get_reference_data,
    store_generated_question, get_questions_by_status, update_question_status,
    get_courses, get_streams_by_course, get_subjects_by_stream
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
    # Prepare data for OpenAI
    data_for_openai = data.copy()
    data_for_openai['subject'] = subject_for_prompt
    data_for_openai['topic'] = topic_for_prompt
    # Call OpenAI to get question and diagram code with library selection
    result = generate_mcq_and_diagram(data_for_openai)
    
    image_url = None
    if result.get('diagram_code'):
        library_used = result.get('library_used', 'schemdraw')
        image_filename = render_diagram(
            result['diagram_code'], 
            library_used, 
            app.config['UPLOAD_FOLDER']
        )
        if image_filename:
            image_url = f"/static/images/{image_filename}"
    
    response = {
        'question_text': result.get('question_text'),
        'options': result.get('options'),
        'correct_answer': result.get('correct_answer'),
        'explanation': result.get('explanation'),
        'diagram_code': result.get('diagram_code'),
        'diagram_image_url': image_url,
        'library_used': result.get('library_used', 'schemdraw')
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
            'library_used': result.get('library_used', 'schemdraw')
        }
        store_generated_question(db_data)
    
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
    """Get all questions with optional status filter"""
    status = request.args.get('status', 'all')
    questions = get_questions_by_status(status)
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

if __name__ == '__main__':
    # Get host and port from environment variables or use defaults
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print(f"🚀 Starting Flask server on {host}:{port}")
    print(f"📱 Access the application from other devices using your computer's IP address")
    print(f"🌐 Local access: http://localhost:{port}")
    print(f"📋 To find your IP address, run: ipconfig (Windows) or ifconfig (Mac/Linux)")
    
    app.run(host=host, port=port, debug=True) 