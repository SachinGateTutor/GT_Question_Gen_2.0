import os
import sys

# Windows: console often uses cp1252; non-ASCII in logs can raise UnicodeEncodeError without UTF-8 stdio
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

import threading
import uuid
import shutil
import time
import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
from flask import Flask, request, jsonify, send_from_directory, abort
from dotenv import load_dotenv
import jwt
from functools import wraps


# Load environment variables from .env file
load_dotenv()
# Headless servers: ensure matplotlib never picks a GUI backend (tkinter) before diagram imports
os.environ.setdefault("MPLBACKEND", "Agg")

from safe_io import safe_print

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
from services.net_backend_service import coerce_stream_id, extract_topic_summary
from services.ai_explanation_service import ai_explanation_service
from flask_cors import CORS
from flasgger import Swagger
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

# Initialize Swagger for API documentation
# Note: Swagger will register its routes automatically
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
        }
    ],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/api-docs"
}

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "GT Question Generator API",
        "description": "AI-powered MCQ generation API with diagram support. This API provides endpoints for generating educational questions using AI, managing question data, and integrating with external services.",
        "version": "2.0.0",
        "contact": {
            "name": "PragyaAI",
        }
    },
    "basePath": "/",
    "schemes": ["http", "https"],
    "consumes": ["application/json"],
    "produces": ["application/json"],
    "tags": [
        {
            "name": "Question Generation",
            "description": "Endpoints for generating questions using AI"
        },
        {
            "name": "Data Retrieval",
            "description": "Endpoints for fetching courses, streams, subjects, topics"
        },
        {
            "name": "Question Management",
            "description": "Endpoints for managing questions"
        },
        {
            "name": "Admin",
            "description": "Admin endpoints for CRUD operations"
        },
        {
            "name": "Status & Health",
            "description": "Health check and status endpoints"
        }
    ],
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Authorization header using the Bearer scheme. Enter 'Bearer ' followed by your token in the text input below. Example: 'Bearer eyJhbGciOi...'"
        }
    },
    "security": [
        {
            "Bearer": []
        }
    ]
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

def decode_jwt_token(token: str) -> dict:
    """
    Decode JWT token and extract payload without verification.
    Returns the payload as a dictionary.
    """
    try:
        # Remove 'Bearer ' prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
        
        # JWT tokens have 3 parts separated by dots: header.payload.signature
        parts = token.split('.')
        if len(parts) != 3:
            return None
        
        # Decode the payload (second part)
        payload = parts[1]
        
        # Add padding if needed (base64 requires padding)
        padding = 4 - len(payload) % 4
        if padding != 4:
            payload += '=' * padding
        
        # Decode base64
        decoded_bytes = base64.urlsafe_b64decode(payload)
        decoded_dict = json.loads(decoded_bytes)
        
        return decoded_dict
    except Exception as e:
        print(f"Error decoding JWT token: {e}")
        return None

def extract_user_id_from_token(token: str) -> str:
    """
    Extract user ID (sub field) from JWT token.
    Returns user ID as string, or None if extraction fails.
    """
    payload = decode_jwt_token(token)
    if payload and 'sub' in payload:
        return str(payload['sub'])
    return None


def extract_user_type_id_from_token(token: str) -> Optional[int]:
    """
    Extract user type ID from JWT token.
    Returns user type ID as int if available, otherwise None.
    """
    payload = decode_jwt_token(token)
    if not payload:
        return None

    user_type_keys = ['user_type_id', 'userTypeId', 'UserTypeID', 'UserTypeId', 'usertypeid']
    for key in user_type_keys:
        if key in payload and payload[key] is not None:
            try:
                return int(payload[key])
            except (TypeError, ValueError):
                return None
    return None


def extract_stream_id_from_token(token: str) -> Optional[int]:
    """
    Extract stream ID from JWT token.
    Returns stream ID as int if available, otherwise None.
    """
    payload = decode_jwt_token(token)
    if not payload:
        return None
    
    stream_keys = ['stream_id', 'streamId', 'StreamID', 'StreamId']
    for key in stream_keys:
        if key in payload:
            try:
                stream_id = int(payload[key])
                return stream_id if stream_id > 0 else None
            except (TypeError, ValueError):
                return None
    return None


def verify_jwt_signature(token: str) -> Optional[dict]:
    """
    Cryptographically verify the JWT token signature and expiration using PyJWT.
    Returns the decoded payload if valid, otherwise None.
    """
    try:
        if token.startswith('Bearer '):
            token = token[7:]
            
        # Get the secret key (fallback to SECRET_KEY if JWT_SECRET is not explicitly set)
        secret = os.getenv('JWT_SECRET') or os.getenv('SECRET_KEY', 'your_secret_key_here_change_this_in_production')
        
        # Decode and verify the token signature and expiration
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        print("[SECURITY WARNING] JWT Token has expired.")
        return None
    except jwt.InvalidTokenError as e:
        print(f"[SECURITY WARNING] Invalid JWT Signature/Token: {e}")
        return None
    except Exception as e:
        print(f"Error during cryptographic verification: {e}")
        return None

def token_required(f):
    """Decorator to enforce cryptographically verified JWT token authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Unauthorized: Authorization token is missing.'
            }), 401
            
        payload = verify_jwt_signature(token)
        if not payload:
            return jsonify({
                'success': False,
                'error': 'Unauthorized: Invalid, expired, or tampered token.'
            }), 401
            
        # Inject user_id into request context
        request.user_id = payload.get('sub')
        return f(*args, **kwargs)
    return decorated


def get_request_flag_and_group(data: dict) -> Tuple[bool, Optional[int]]:
    """
    Normalize aptitude/group fields from request payload.
    Supports snake_case and camelCase keys for compatibility.
    """
    if not isinstance(data, dict):
        return False, None

    is_aptitude_raw = data.get('is_aptitude', data.get('isAptitude', False))
    is_aptitude = str(is_aptitude_raw).strip().lower() in ('1', 'true', 'yes', 'on') if isinstance(is_aptitude_raw, str) else bool(is_aptitude_raw)

    raw_group_id = data.get('group_id', data.get('groupId'))
    if raw_group_id in (None, ''):
        return is_aptitude, None

    try:
        return is_aptitude, int(raw_group_id)
    except (TypeError, ValueError):
        return is_aptitude, None

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
        
        print("[START] Starting integrated image monitoring...")
        print(f"[INFO] Monitoring: {project_root}")
        print(f"[INFO] Destination: {images_dir}")
        
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
                            print(f"[REPLACE] Replaced existing: {filename}")
                        else:
                            print(f"[NEW] New file: {filename}")
                        
                        # Move the file
                        shutil.move(str(source_path), str(dest_path))
                        print(f"[OK] Moved: {filename} -> static/images/")
                        
                    except Exception as e:
                        print(f"[ERROR] Error moving {filename}: {e}")
                
                # Sleep before next check
                time.sleep(2)
                
            except Exception as e:
                print(f"[ERROR] Image monitoring error: {e}")
                time.sleep(5)
    
    # Start monitoring thread
    image_monitor_thread = threading.Thread(target=monitor_images, daemon=True)
    image_monitor_thread.start()
    print("[OK] Image monitoring started successfully")

def stop_image_monitoring():
    """Stop image monitoring"""
    global image_monitor_running
    image_monitor_running = False
    print("[STOP] Image monitoring stopped")

# Start image monitoring when app starts
def initialize_app():
    """Initialize the application and start image monitoring"""
    try:
        start_image_monitoring()
    except Exception as e:
        print(f"[WARNING] Could not start image monitoring: {e}")

# Initialize app when Flask starts
with app.app_context():
    initialize_app()

# Serve the main HTML file
@app.route('/')
def index():
    return send_from_directory('..', 'index.html')

# Serve static files (config.js, etc.)
# IMPORTANT: This catch-all route must exclude Swagger paths
@app.route('/<path:filename>')
def serve_static(filename):
    # Exclude Swagger and API routes from static file serving
    # These should be handled by their respective route handlers
    excluded = ['api-docs', 'apispec.json', 'flasgger_static', 'api']
    if any(filename == ex or filename.startswith(ex + '/') for ex in excluded):
        abort(404)
    
    # Block hidden files and directories (dotfiles like .env)
    if filename.startswith('.') or '/.' in filename or '\\.' in filename:
        abort(404)
        
    # Check if it's an image file in static/images
    if filename.startswith('static/images/'):
        # Serve from app directory (images are in app/static/images/)
        return send_from_directory('.', filename)
    else:
        # Serve other static files from root directory
        return send_from_directory('..', filename)

@app.route('/api/generate', methods=['POST'])
@token_required
def generate():
    """
    Generate MCQ questions with optional diagrams
    ---
    tags:
      - Question Generation
    summary: Generate one or more MCQ questions
    description: Generates MCQ questions using AI with optional diagram support. Supports multiple question generation in a single request.
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        description: Question generation parameters
        required: true
        schema:
          type: object
          required:
            - subject_id
            - topic_id
          properties:
            subject_id:
              type: integer
              description: Subject ID
              example: 1
            topic_id:
              type: integer
              description: Topic ID
              example: 1
            question_type_id:
              type: integer
              description: "Question type ID (default: 1 for MCQ)"
              example: 1
            bloom_level_id:
              type: integer
              description: "Bloom taxonomy level ID (1-6)"
              example: 3
            difficulty_level_id:
              type: integer
              description: Difficulty level ID
              example: 2
            requires_diagram:
              type: boolean
              description: Whether to include a diagram
              example: true
            requires_option_diagrams:
              type: boolean
              description: Whether to include diagrams for each option
              example: false
            num_questions:
              type: integer
              description: Number of questions to generate
              example: 1
            custom_prompt:
              type: string
              description: Custom prompt for question generation
              example: "Focus on practical applications"
    responses:
      200:
        description: Question(s) generated successfully
        schema:
          type: object
          properties:
            question_id:
              type: integer
              description: Database ID of the generated question
            question_text:
              type: string
              description: The question text
            options:
              type: array
              items:
                type: string
              description: "Answer options (A, B, C, D)"
            correct_answer:
              type: string
              description: Correct answer option
            explanation:
              type: string
              description: Explanation of the answer
            diagram_image_url:
              type: string
              description: "URL to the generated diagram image (if applicable)"
            library_used:
              type: string
              description: "Diagram library used (schemdraw, matplotlib, etc.)"
            option_images:
              type: array
              items:
                type: string
              description: "URLs to option diagram images (if applicable)"
            all_questions:
              type: array
              description: Array of all generated questions
            total_generated:
              type: integer
              description: Total number of questions generated
      500:
        description: Error generating question
        schema:
          type: object
          properties:
            success:
              type: boolean
              example: false
            error:
              type: string
              example: "Error message"
    """
    data = request.get_json()
    num_questions = data.get('num_questions', 1)
    
    # Look up subject and topic names from IDs
    subject_id = data.get('subject_id')
    topic_id = data.get('topic_id')
    subject_name = None
    topic_name = None
    topic_summary = None
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

    # If DB lookup failed/disabled, try getting names from .NET Backend service
    if not subject_name or not topic_name:
        auth_header = request.headers.get('Authorization')
        token = None
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(" ")[1]
        
        is_aptitude = data.get('isAptitude', False)
        group_id = data.get('groupId') or data.get('group_id')
        
        from services.net_backend_service import net_backend_service
        
        if not subject_name and subject_id:
            try:
                subject_res = net_backend_service.get_subject_by_id(
                    subject_id=subject_id,
                    auth_token=token,
                    stream_id=coerce_stream_id(data.get('stream_id')),
                    is_aptitude=is_aptitude,
                    group_id=group_id
                )
                if subject_res.get('success'):
                    subject_name = subject_res.get('subject_name')
                    print(f"[OK] Dynamically fetched subject name from .NET backend: {subject_name}")
            except Exception as e:
                print(f"[WARN] Failed to get subject name from .NET backend: {e}")
                
        if not topic_name and topic_id and subject_id:
            try:
                topic_res = net_backend_service.get_topic_by_id(
                    topic_id=topic_id,
                    subject_id=subject_id,
                    auth_token=token,
                    is_aptitude=is_aptitude,
                    group_id=group_id,
                    stream_id=coerce_stream_id(data.get('stream_id'))
                )
                if topic_res.get('success'):
                    topic_name = topic_res.get('topic_name')
                    topic_summary = extract_topic_summary(topic_res)
                    print(f"[OK] Dynamically fetched topic name from .NET backend: {topic_name}")
            except Exception as e:
                print(f"[WARN] Failed to get topic name from .NET backend: {e}")

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
            if topic_summary:
                data_for_openai['topic_summary'] = topic_summary
        
            # Call OpenAI to get question and diagram code with library selection
            result = generate_mcq_and_diagram(data_for_openai)
            if not result or result.get('error'):
                generation_error = result.get('error') if isinstance(result, dict) else 'Unknown generation failure'
                raise ValueError(generation_error)
        
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
                    print(f"[OK] Diagram generated successfully: {image_filename}")
                else:
                    print(f"[ERROR] Diagram generation failed completely for {library_used}")
                    print(f"[RETRY] Attempting to generate replacement question...")
                    
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
                                print(f"[OK] Generated replacement question successfully")
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
                                        print(f"[OK] Replacement question diagram generated: {replacement_image_filename}")
                                    else:
                                        print(f"[ERROR] Replacement question diagram also failed, proceeding without diagram")
                                        print(f"[NOTE] No misleading diagram will be shown - better for educational accuracy")
                                        image_url = None
                                else:
                                    print(f"[ERROR] Replacement question has no diagram code")
                                    image_url = None
                            else:
                                print(f"[ERROR] Failed to generate replacement question, proceeding with original")
                                image_url = None
                        except Exception as replacement_error:
                            print(f"[ERROR] Replacement question generation failed: {replacement_error}")
                            image_url = None
                    else:
                        print(f"[INFO] Diagram not required, proceeding without diagram")
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
                            print(f"[DEBUG] Failed to render option {option} diagram, generating fallback")
                            # Fallback: generate a default diagram
                            option_images.append(None)
                    else:
                        # Generate fallback diagram for missing option
                        print(f"[DEBUG] No code for option {option}, generating fallback")
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
                    print(" Auto-detecting Bloom level for question...")
                    detected_bloom_level = detect_bloom_level(
                        result.get('question_text'),
                        result.get('options', []),
                        result.get('explanation', '')
                    )
                    if detected_bloom_level:
                        bloom_level_id = detected_bloom_level
                        print(f"[OK] Bloom level auto-detected: {detected_bloom_level}")
                    else:
                        bloom_level_id = None  # Default to None if detection fails
                        print("[WARNING] Bloom level detection failed, using None")
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
        print(f"[ERROR] Error in generate endpoint: {str(e)}")
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
@token_required
def generate_cdq():
    """
    Generate CDQ (Context Dependent Question) with diagram
    ---
    tags:
      - Question Generation
    summary: Generate CDQ with passage and multiple questions
    description: Generates a Context Dependent Question (CDQ) with a passage and 4 related questions
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - topic_id
            - subject_id
            - stream_id
            - course_id
          properties:
            topic_id:
              type: integer
            subject_id:
              type: integer
            stream_id:
              type: integer
            course_id:
              type: integer
            context_type:
              type: string
              default: real_world
            difficulty_level_id:
              type: integer
              default: 2
            bloom_level_id:
              type: integer
              default: 2
            requires_diagram:
              type: boolean
              default: false
    responses:
      200:
        description: CDQ generated successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            passage_id:
              type: integer
            question_ids:
              type: array
              items:
                type: integer
            passage_text:
              type: string
            questions:
              type: array
            total_questions:
              type: integer
      400:
        description: Missing required parameters
      500:
        description: Error generating CDQ
    """
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
            print(f" Debug: Storing CDQ passage with data: {passage_data}")
            passage_id = insert_cdq_passage(passage_data)
            print(f" Debug: CDQ passage stored with ID: {passage_id}")
            
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
                    print(f" Debug: CDQ generation successful - Passage ID: {passage_id}, Question IDs: {stored_questions}")
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
@token_required
def get_courses_api():
    """
    Get all active courses
    ---
    tags:
      - Data Retrieval
    summary: Retrieve all active courses
    description: Returns a list of all active courses in the system
    produces:
      - application/json
    responses:
      200:
        description: List of courses
        schema:
          type: array
          items:
            type: object
            properties:
              CourseID:
                type: integer
              CourseName:
                type: string
      500:
        description: Server error
    """
    try:
        courses = get_courses()
        return jsonify(courses)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/streams/<int:course_id>', methods=['GET'])
@token_required
def get_streams_api(course_id):
    """
    Get streams by course ID
    ---
    tags:
      - Data Retrieval
    summary: Retrieve streams for a specific course
    produces:
      - application/json
    parameters:
      - name: course_id
        in: path
        type: integer
        required: true
        description: Course ID
    responses:
      200:
        description: List of streams
        schema:
          type: array
          items:
            type: object
            properties:
              StreamID:
                type: integer
              StreamName:
                type: string
    """
    streams = get_streams_by_course(course_id)
    return jsonify(streams)

@app.route('/api/subjects', methods=['GET'])
@token_required
def get_subjects_api():
    """
    Get subjects
    ---
    tags:
      - Data Retrieval
    summary: Retrieve subjects (optionally filtered by stream)
    produces:
      - application/json
    parameters:
      - name: stream_id
        in: query
        type: integer
        required: false
        description: Filter subjects by stream ID
    responses:
      200:
        description: List of subjects
        schema:
          type: array
          items:
            type: object
            properties:
              SubjectID:
                type: integer
              SubjectName:
                type: string
    """
    stream_id = request.args.get('stream_id')
    if stream_id:
        subjects = get_subjects_by_stream(int(stream_id))
    else:
        subjects = get_subjects()
    return jsonify(subjects)

@app.route('/api/topics/<int:subject_id>', methods=['GET'])
@token_required
def get_topics_api(subject_id):
    """
    Get topics for a specific subject
    ---
    tags:
      - Data Retrieval
    summary: Retrieve topics for a specific subject
    produces:
      - application/json
    parameters:
      - name: subject_id
        in: path
        type: integer
        required: true
        description: Subject ID
    responses:
      200:
        description: List of topics
        schema:
          type: array
          items:
            type: object
            properties:
              TopicID:
                type: integer
              TopicName:
                type: string
              BloomLevelID:
                type: integer
    """
    topics = get_topics_by_subject(subject_id)
    return jsonify(topics)

@app.route('/api/reference/<table_name>', methods=['GET'])
@token_required
def get_reference_api(table_name):
    """
    Get reference data for dropdowns
    ---
    tags:
      - Data Retrieval
    summary: Retrieve reference data (QuestionType, BloomLevel, DifficultyLevel, etc.)
    produces:
      - application/json
    parameters:
      - name: table_name
        in: path
        type: string
        required: true
        enum: [QuestionType, BloomLevel, DifficultyLevel, SectionType]
        description: Reference table name
    responses:
      200:
        description: Reference data
        schema:
          type: array
      400:
        description: Invalid table name
    """
    allowed_tables = ['QuestionType', 'BloomLevel', 'DifficultyLevel', 'SectionType']
    if table_name not in allowed_tables:
        return jsonify({'error': 'Invalid table name'}), 400
    
    data = get_reference_data(table_name)
    return jsonify(data)

# API endpoints for question management
@app.route('/api/questions', methods=['GET'])
@token_required
def get_questions_api():
    """
    Get all questions with optional filters
    ---
    tags:
      - Question Management
    summary: Retrieve questions with filters
    produces:
      - application/json
    parameters:
      - name: status
        in: query
        type: string
        enum: [all, pending, approved, discarded]
        description: Question status filter
      - name: course
        in: query
        type: string
        description: Filter by course name
      - name: stream
        in: query
        type: string
        description: Filter by stream name
      - name: subject
        in: query
        type: string
        description: Filter by subject name
      - name: topic
        in: query
        type: string
        description: Filter by topic name
      - name: difficulty
        in: query
        type: string
        description: Filter by difficulty level
      - name: bloom
        in: query
        type: string
        description: Filter by Bloom level
      - name: questionType
        in: query
        type: string
        description: Filter by question type
    responses:
      200:
        description: List of questions
        schema:
          type: array
    """
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
@token_required
def update_question_status_api(question_id):
    """
    Update question status
    ---
    tags:
      - Question Management
    summary: Approve or discard a question
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: question_id
        in: path
        type: integer
        required: true
        description: Question ID
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - status
          properties:
            status:
              type: string
              enum: [approved, discarded]
              description: New status for the question
    responses:
      200:
        description: Status updated successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
      400:
        description: Invalid status
    """
    data = request.get_json()
    status = data.get('status')
    
    if status not in ['approved', 'discarded']:
        return jsonify({'error': 'Invalid status'}), 400
    
    success = update_question_status(question_id, status)
    return jsonify({'success': success})

@app.route('/api/explain-question', methods=['POST'])
@token_required
def explain_question_api():
    """
    Generate AI explanation for a question
    ---
    tags:
      - Question Management
    summary: Generate AI-powered explanation for a question
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - question_text
          properties:
            question_id:
              type: integer
            question_text:
              type: string
            options:
              type: array
              items:
                type: string
            correct_answer:
              type: string
            topic:
              type: string
            subject:
              type: string
            difficulty_level:
              type: string
            question_type:
              type: string
            bloom_level:
              type: string
    responses:
      200:
        description: Explanation generated successfully
      400:
        description: Missing required fields
      500:
        description: Server error
    """
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
@token_required
def admin_courses():
    """
    Admin: Manage courses
    ---
    tags:
      - Admin
    summary: Get all courses or create a new course
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            CourseName:
              type: string
    responses:
      200:
        description: Success
      405:
        description: Method not allowed
    """
    if request.method == 'GET':
        return jsonify(get_all_courses())
    elif request.method == 'POST':
        data = request.get_json()
        success = add_course(data['CourseName'])
        return jsonify({'success': success, 'message': 'Course added successfully' if success else 'Failed to add course'})
    return abort(405)

@app.route('/api/admin/courses/<int:course_id>', methods=['PUT', 'DELETE'])
@token_required
def admin_course_modify(course_id):
    """
    Admin: Update or delete course
    ---
    tags:
      - Admin
    summary: Update or delete a course
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - name: course_id
        in: path
        type: integer
        required: true
      - in: body
        name: body
        required: false
        schema:
          type: object
          properties:
            CourseName:
              type: string
    responses:
      200:
        description: Success
      405:
        description: Method not allowed
    """
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
@token_required
def admin_streams():
    if request.method == 'GET':
        return jsonify(get_all_streams())
    elif request.method == 'POST':
        data = request.get_json()
        success = add_stream(data['CourseID'], data['StreamName'])
        return jsonify({'success': success, 'message': 'Stream added successfully' if success else 'Failed to add stream'})
    return abort(405)

@app.route('/api/admin/streams/<int:stream_id>', methods=['PUT', 'DELETE'])
@token_required
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
@token_required
def admin_subjects():
    if request.method == 'GET':
        return jsonify(get_all_subjects())
    elif request.method == 'POST':
        data = request.get_json()
        success = add_subject(data['StreamID'], data['SubjectName'])
        return jsonify({'success': success, 'message': 'Subject added successfully' if success else 'Failed to add subject'})
    return abort(405)

@app.route('/api/admin/subjects/<int:subject_id>', methods=['PUT', 'DELETE'])
@token_required
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
@token_required
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
@token_required
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
@token_required
def analyze_topic():
    """
    Analyze topic and return AI recommendations
    ---
    tags:
      - Question Generation
    summary: Analyze topic and get AI recommendations for question generation
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            course_id:
              type: integer
            stream_id:
              type: integer
            subject_id:
              type: integer
            topic_id:
              type: integer
            question_type:
              type: string
    responses:
      200:
        description: Analysis completed successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            analysis:
              type: object
            topic_info:
              type: object
      500:
        description: Analysis failed
    """
    try:
        data = request.json
        
        # Extract token if provided (optional - for tracking/logging)
        auth_header = request.headers.get('Authorization', '')
        token = None
        user_id = None
        if auth_header:
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
            else:
                token = auth_header
            user_id = extract_user_id_from_token(token)
            if user_id:
                print(f"Topic analysis requested by user: {user_id}")
        
        # Also check if token is in body (frontend may send it there)
        if not token and data.get('token'):
            token = data.get('token')
            user_id = extract_user_id_from_token(token)
            if user_id:
                print(f"Topic analysis requested by user: {user_id}")
        
        course_id = data.get('course_id')
        stream_id = coerce_stream_id(data.get('stream_id')) 
        subject_id = data.get('subject_id')
        topic_id = data.get('topic_id')
        question_type = data.get('question_type')
        is_aptitude, group_id = get_request_flag_and_group(data)
        
        # Fetch real names from .NET backend
        from services.net_backend_service import net_backend_service
        
        # Initialize with fallback values
        topic_name = f"Topic {topic_id}" if topic_id else "Unknown Topic"
        subject_name = f"Subject {subject_id}" if subject_id else "Unknown Subject"
        stream_name = f"Stream {stream_id}" if stream_id else "Unknown Stream"
        course_name = f"Course {course_id}" if course_id else "Unknown Course"
        bloom_level_name = 'Intermediate'  # Default
        
        # Get topic name and details from .NET backend
        if topic_id:
            topic_result = net_backend_service.get_topic_by_id(
                topic_id,
                subject_id,
                auth_token=token,
                is_aptitude=is_aptitude,
                group_id=group_id,
                stream_id=coerce_stream_id(stream_id)
            )
            if topic_result.get('success') and topic_result.get('topic_name'):
                topic_name = topic_result['topic_name']
                print(f" Retrieved topic name: {topic_name} for topic_id: {topic_id}")
                
                # Check if topic data includes stream/course info
                topic_data = topic_result.get('data', {})
                if topic_data:
                    # Try to get stream name from topic data
                    stream_name_from_topic = (topic_data.get('streamName') or 
                                             topic_data.get('StreamName') or
                                             topic_data.get('stream_name'))
                    if stream_name_from_topic:
                        stream_name = stream_name_from_topic
                    
                    # Try to get course name from topic data
                    course_name_from_topic = (topic_data.get('courseName') or 
                                            topic_data.get('CourseName') or
                                            topic_data.get('course_name'))
                    if course_name_from_topic:
                        course_name = course_name_from_topic
                    
                    # Try to get bloom level from topic data
                    bloom_level_from_topic = (topic_data.get('bloomLevelName') or 
                                             topic_data.get('BloomLevelName') or
                                             topic_data.get('bloom_level_name'))
                    if bloom_level_from_topic:
                        bloom_level_name = bloom_level_from_topic
            else:
                print(f" Warning: Could not retrieve topic name for topic_id: {topic_id}, using fallback")
        
        # Get subject name from .NET backend
        if subject_id:
            subject_result = net_backend_service.get_subject_by_id(
                subject_id,
                auth_token=token,
                stream_id=stream_id,
                is_aptitude=is_aptitude,
                group_id=group_id
            )
            if subject_result.get('success') and subject_result.get('subject_name'):
                subject_name = subject_result['subject_name']
                print(f" Retrieved subject name: {subject_name} for subject_id: {subject_id}")
                
                # Check if subject data includes stream/course info
                subject_data = subject_result.get('data', {})
                if subject_data:
                    # Try to get stream name from subject data
                    stream_name_from_subject = (subject_data.get('streamName') or 
                                              subject_data.get('StreamName') or
                                              subject_data.get('stream_name'))
                    if stream_name_from_subject:
                        stream_name = stream_name_from_subject
                    
                    # Try to get course name from subject data
                    course_name_from_subject = (subject_data.get('courseName') or 
                                               subject_data.get('CourseName') or
                                               subject_data.get('course_name'))
                    if course_name_from_subject:
                        course_name = course_name_from_subject
            else:
                print(f" Warning: Could not retrieve subject name for subject_id: {subject_id}, using fallback")
        
        # Try to get stream name from .NET backend if still using fallback
        if stream_id and stream_name.startswith('Stream '):
            try:
                stream_result = net_backend_service.get_stream_by_id(stream_id, auth_token=token)
                if stream_result.get('success') and stream_result.get('stream_name'):
                    stream_name = stream_result['stream_name']
                    print(f" Retrieved stream name from .NET backend: {stream_name}")
            except Exception as e:
                print(f" Warning: Could not retrieve stream name from .NET backend: {e}")
        
        # Create topic info with real names
        topic_info = {
            'topic_id': topic_id,
            'subject_id': subject_id,
            'stream_id': stream_id,
            'course_id': course_id,
            'topic_name': topic_name,
            'subject_name': subject_name,
            'stream_name': stream_name,
            'course_name': course_name,
            'bloom_level_name': bloom_level_name
        }
        
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
@token_required
def generate_random_questions():
    """
    Generate random questions with real-time progress
    ---
    tags:
      - Question Generation
    summary: Generate multiple questions based on AI analysis
    description: Starts background generation of questions and returns a generation ID for progress tracking
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            question_plan:
              type: object
              properties:
                total_questions:
                  type: integer
                diagram_questions:
                  type: integer
                option_diagram_questions:
                  type: integer
                text_only_questions:
                  type: integer
                code_questions:
                  type: integer
    responses:
      200:
        description: Generation started successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            generation_id:
              type: string
              description: ID to track generation progress
      500:
        description: Generation failed to start
    """
    try:
        data = request.json
        question_plan = data.get('question_plan')
        
        # Extract token and user_id (required)
        auth_header = request.headers.get('Authorization', '')
        token = None
        user_id = None
        if auth_header:
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]
            else:
                token = auth_header
            user_id = extract_user_id_from_token(token)
            if not user_id:
                print(f"Warning: Could not extract user ID from token")
        
        # Also check if token is in body (frontend may send it there)
        if not token and data.get('token'):
            token = data.get('token')
            user_id = extract_user_id_from_token(token)
            if not user_id:
                print(f"Warning: Could not extract user ID from token")
        
        # Return 401 if token is missing
        if not token:
            return jsonify({
                'success': False,
                'error': 'Authentication token required'
            }), 401
        
        generation_id = str(uuid.uuid4())
        
        # Store generation session with auth_token and user_id
        active_generations[generation_id] = {
            'status': 'active',
            'auth_token': token,
            'user_id': user_id,
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
@token_required
def get_generation_progress(generation_id):
    """
    Get generation progress
    ---
    tags:
      - Question Generation
    summary: Get real-time progress of question generation
    produces:
      - application/json
    parameters:
      - name: generation_id
        in: path
        type: string
        required: true
        description: Generation ID returned from generate-random
    responses:
      200:
        description: Generation progress
        schema:
          type: object
          properties:
            success:
              type: boolean
            progress:
              type: object
              properties:
                current:
                  type: integer
                total:
                  type: integer
            status:
              type: string
              enum: [active, completed, stopped, error]
            generated_questions:
              type: array
      404:
        description: Generation not found
    """
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
@token_required
def stop_generation(generation_id):
    """
    Stop question generation
    ---
    tags:
      - Question Generation
    summary: Stop an ongoing question generation process
    produces:
      - application/json
    parameters:
      - name: generation_id
        in: path
        type: string
        required: true
        description: Generation ID to stop
    responses:
      200:
        description: Generation stopped successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
      404:
        description: Generation not found
    """
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
        
        # Get auth_token and user_id from session
        auth_token = session.get('auth_token')
        user_id = session.get('user_id')
        
        # Import net_backend_service
        from services.net_backend_service import net_backend_service
        
        from services.difficulty_prompts import build_question_level_plan

        # Generate each type of question
        question_types = [
            ('diagram', question_plan['diagram_questions']),
            ('option_diagram', question_plan['option_diagram_questions']),
            ('text_only', question_plan['text_only_questions']),
            ('code', question_plan['code_questions'])
        ]

        generation_queue = []
        for q_type, count in question_types:
            generation_queue.extend([q_type] * int(count or 0))
        level_plan = build_question_level_plan(len(generation_queue))
        
        for i, q_type in enumerate(generation_queue):
            if session['status'] == 'stopped':
                break

            difficulty_level_id, bloom_level_id = level_plan[i] if i < len(level_plan) else (2, 3)

            question_data = generate_single_question(
                request_data,
                q_type,
                auth_token=auth_token,
                difficulty_level_id=difficulty_level_id,
                bloom_level_id=bloom_level_id
            )

            if question_data is None:
                print(f" Question generation skipped due to missing subject/topic data")
                progress['current'] += 1
                progress[f'{q_type}_current'] += 1
                session['generated_questions'].append({
                    'id': None,
                    'jkuh': None,
                    'type': q_type,
                    'error': 'Failed to retrieve subject/topic names from backend'
                })
                continue

            if question_data:
                if 'generation_id' not in question_data:
                    question_data['generation_id'] = generation_id

                storage_result = net_backend_service.store_question(
                    question_data,
                    auth_token=auth_token,
                    user_id=user_id,
                    user_type_id=extract_user_type_id_from_token(auth_token) if auth_token else None
                )

                question_id = None
                jkuh = None
                if storage_result.get('success'):
                    question_id = storage_result.get('question_id')
                    jkuh = storage_result.get('jkuh')
                    print(f" Question stored successfully with ID: {question_id}, jkuh: {jkuh}")
                    question_data['question_id'] = question_id
                    question_data['jkuh'] = jkuh

                progress['current'] += 1
                progress[f'{q_type}_current'] += 1

                session['generated_questions'].append({
                    'id': question_id,
                    'jkuh': jkuh,
                    'type': q_type,
                    'question': question_data
                })
            else:
                print(f" Failed to store question: {storage_result.get('error', 'Unknown error')}")
                progress['current'] += 1
                progress[f'{q_type}_current'] += 1
                session['generated_questions'].append({
                    'id': None,
                    'jkuh': None,
                    'type': q_type,
                    'question': question_data,
                    'error': storage_result.get('error', 'Storage failed')
                })
        
        # Mark as completed
        if session['status'] != 'stopped':
            session['status'] = 'completed'
            
    except Exception as e:
        print(f"Background generation error: {str(e)}")
        session['status'] = 'error'
        session['error'] = str(e)

def generate_single_question(request_data, question_type, auth_token=None, difficulty_level_id=None, bloom_level_id=None):
    """Generate a single question based on type"""
    from services.difficulty_prompts import difficulty_name_from_id, bloom_name_from_id

    enhanced_request = request_data.copy()
    if difficulty_level_id is not None:
        enhanced_request['difficulty_level_id'] = difficulty_level_id
        enhanced_request['difficulty_level'] = difficulty_name_from_id(difficulty_level_id)
    if bloom_level_id is not None:
        enhanced_request['bloom_level_id'] = bloom_level_id
        enhanced_request['bloom_level'] = bloom_name_from_id(bloom_level_id)
    
    # Fetch subject and topic names from .NET backend before generating question
    # This ensures the AI generates questions for the correct subject/topic, not defaulting to "Programming"
    subject_id = request_data.get('subject_id')
    topic_id = request_data.get('topic_id')
    stream_id = coerce_stream_id(request_data.get('stream_id'))
    is_aptitude, group_id = get_request_flag_and_group(request_data)
    
    if not stream_id and auth_token:
        stream_id = extract_stream_id_from_token(auth_token)
        if stream_id:
            enhanced_request['stream_id'] = stream_id
    elif stream_id:
        enhanced_request['stream_id'] = stream_id
    
    subject_name = None
    topic_name = None
    stream_name = None
    
    # Import net_backend_service
    from services.net_backend_service import net_backend_service
    
    # Get subject name from .NET backend
    if subject_id:
        try:
            subject_result = net_backend_service.get_subject_by_id(
                subject_id,
                auth_token=auth_token,
                stream_id=stream_id,
                is_aptitude=is_aptitude,
                group_id=group_id
            )
            print(f" Debug: Subject fetch result for subject_id {subject_id}: {subject_result}")
            if subject_result.get('success') and subject_result.get('subject_name'):
                subject_name = subject_result['subject_name']
                print(f" Retrieved subject name: {subject_name} for subject_id: {subject_id}")
                enhanced_request['subject'] = subject_name
                
                # Extract stream_id from subject data if available and not already set
                if not stream_id and subject_result.get('data'):
                    subject_data = subject_result['data']
                    stream_id_from_subject = (subject_data.get('streamId') or 
                                            subject_data.get('StreamID') or
                                            subject_data.get('stream_id'))
                    if stream_id_from_subject:
                        stream_id = stream_id_from_subject
                        print(f" Extracted stream_id: {stream_id} from subject data")
            else:
                error_msg = subject_result.get('error', 'Unknown error')
                print(f" ERROR: Could not retrieve subject name for subject_id: {subject_id}. Error: {error_msg}")
                # DO NOT use fallback - return None to prevent wrong data insertion
                print(f" CRITICAL: Cannot proceed without valid subject name. Skipping question generation.")
                return None
        except Exception as e:
            print(f" EXCEPTION: Error fetching subject {subject_id}: {e}")
            import traceback
            traceback.print_exc()
            # DO NOT use fallback - return None to prevent wrong data insertion
            print(f" CRITICAL: Cannot proceed without valid subject name. Skipping question generation.")
            return None
    else:
        print(f" CRITICAL ERROR: No subject_id provided in request_data. Cannot proceed.")
        return None
    
    # Get topic name from .NET backend
    if topic_id:
        try:
            topic_result = net_backend_service.get_topic_by_id(
                topic_id,
                subject_id,
                auth_token=auth_token,
                is_aptitude=is_aptitude,
                group_id=group_id,
                stream_id=stream_id
            )
            print(f" Debug: Topic fetch result for topic_id {topic_id}: {topic_result}")
            if topic_result.get('success') and topic_result.get('topic_name'):
                topic_name = topic_result['topic_name']
                print(f" Retrieved topic name: {topic_name} for topic_id: {topic_id}")
                enhanced_request['topic'] = topic_name
                topic_summary = extract_topic_summary(topic_result)
                if topic_summary:
                    enhanced_request['topic_summary'] = topic_summary
            else:
                error_msg = topic_result.get('error', 'Unknown error')
                print(f" ERROR: Could not retrieve topic name for topic_id: {topic_id}. Error: {error_msg}")
                # DO NOT use fallback - return None to prevent wrong data insertion
                print(f" CRITICAL: Cannot proceed without valid topic name. Skipping question generation.")
                return None
        except Exception as e:
            print(f" EXCEPTION: Error fetching topic {topic_id}: {e}")
            import traceback
            traceback.print_exc()
            # DO NOT use fallback - return None to prevent wrong data insertion
            print(f" CRITICAL: Cannot proceed without valid topic name. Skipping question generation.")
            return None
    else:
        print(f" CRITICAL ERROR: No topic_id provided in request_data. Cannot proceed.")
        return None
    
    # Get stream name if available (optional, for better context)
    # Do this BEFORE logging final values
    if stream_id:
        try:
            stream_result = net_backend_service.get_stream_by_id(stream_id, auth_token=auth_token)
            if stream_result.get('success') and stream_result.get('stream_name'):
                stream_name = stream_result['stream_name']
                enhanced_request['stream'] = stream_name
                print(f" Retrieved stream name: {stream_name} for stream_id: {stream_id}")
        except Exception as e:
            print(f" Warning: Could not retrieve stream name: {e}")
    
    # CRITICAL: Ensure subject and topic are set before calling AI
    # DO NOT proceed with fallbacks - fail safely if data is missing
    if not enhanced_request.get('subject'):
        print(f" CRITICAL ERROR: Subject is missing! Cannot proceed with question generation.")
        return None
    if not enhanced_request.get('topic'):
        print(f" CRITICAL ERROR: Topic is missing! Cannot proceed with question generation.")
        return None
    
    # Log what we're passing to the AI
    print(f" FINAL: Passing to AI - subject: '{enhanced_request.get('subject')}', topic: '{enhanced_request.get('topic')}', stream: '{enhanced_request.get('stream')}', difficulty: '{enhanced_request.get('difficulty_level')}', bloom: '{enhanced_request.get('bloom_level')}'")
    
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
            'stream_id': stream_id or request_data.get('stream_id'),
            'question_type_id': 1,  # MCQ
            'bloom_level_id': bloom_level_id if bloom_level_id is not None else request_data.get('bloom_level_id', 1),
            'difficulty_level_id': difficulty_level_id if difficulty_level_id is not None else request_data.get('difficulty_level_id', 1),
            'marks': 1,
            'is_aptitude': is_aptitude,
            'group_id': group_id
        })
        
        # Handle diagram rendering if needed
        if generated_data.get('diagram_code'):
            try:
                import os
                # Set the output folder for diagram images
                output_folder = app.config['UPLOAD_FOLDER']
                diagram_result = render_diagram(generated_data['diagram_code'], generated_data.get('library_used'), output_folder)
                
                # render_diagram() returns a filename string, not a dict
                if isinstance(diagram_result, str):
                    # It's a filename, create the full URL path
                    generated_data['diagram_image_url'] = f"/static/images/{diagram_result}"
                    print(f" Diagram image URL set: {generated_data['diagram_image_url']}")
                elif isinstance(diagram_result, dict) and diagram_result.get('image_url'):
                    # Handle dict format if it ever changes
                    generated_data['diagram_image_url'] = diagram_result['image_url']
                else:
                    generated_data['diagram_image_url'] = None
                    print(f" Warning: Diagram rendering returned unexpected format: {type(diagram_result)}")
            except Exception as e:
                print(f"Diagram rendering error: {e}")
                import traceback
                traceback.print_exc()
                generated_data['diagram_image_url'] = None
        
        # Handle option diagrams if needed
        if generated_data.get('option_diagram_codes'):
            option_images = []
            for option, code in generated_data['option_diagram_codes'].items():
                if code:
                    try:
                        import os
                        # Set the output folder for diagram images
                        output_folder = app.config['UPLOAD_FOLDER']
                        diagram_result = render_diagram(code, generated_data.get('library_used'), output_folder)
                        
                        # render_diagram() returns a filename string, not a dict
                        if isinstance(diagram_result, str):
                            # It's a filename, create the full URL path
                            option_images.append(f"/static/images/{diagram_result}")
                        elif isinstance(diagram_result, dict) and diagram_result.get('image_url'):
                            # Handle dict format if it ever changes
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

# ============================================================================
# .NET BACKEND INTEGRATION ENDPOINTS
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    ---
    tags:
      - Status & Health
    summary: Check API health status
    description: Returns the health status of the Python service and .NET backend connection
    produces:
      - application/json
    responses:
      200:
        description: Service health status
        schema:
          type: object
          properties:
            status:
              type: string
              description: "Overall status (healthy, degraded, unhealthy)"
              example: "healthy"
            python_service:
              type: string
              description: Python service status
              example: "running"
            net_backend:
              type: string
              description: .NET backend connection status
              example: "connected"
            timestamp:
              type: string
              format: date-time
              description: Timestamp of the health check
      500:
        description: Service unhealthy
        schema:
          type: object
          properties:
            status:
              type: string
              example: "unhealthy"
            error:
              type: string
              example: "Error message"
    """
    try:
        # Check if our service is healthy
        from services.net_backend_service import net_backend_service
        
        # Check .NET backend health
        net_health = net_backend_service.health_check()
        
        if net_health['success']:
            return jsonify({
                "status": "healthy",
                "python_service": "running",
                "net_backend": "connected",
                "timestamp": datetime.now().isoformat()
            }), 200
        else:
            return jsonify({
                "status": "degraded",
                "python_service": "running", 
                "net_backend": "unavailable",
                "error": net_health.get('error', 'Unknown error'),
                "timestamp": datetime.now().isoformat()
            }), 200  # Still return 200 as our service is healthy
            
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "python_service": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/generate-question', methods=['POST'])
@token_required
def generate_single_question_endpoint():
    """
    Generate single question for .NET backend
    ---
    tags:
      - Question Generation
    summary: Generate a single question for .NET backend integration
    description: This endpoint is used by the .NET backend to generate questions via the Python AI service
    consumes:
      - application/json
    produces:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - generation_id
            - subject_id
            - topic_id
          properties:
            generation_id:
              type: string
            subject_id:
              type: integer
            topic_id:
              type: integer
            section_id:
              type: integer
              default: 0
            question_type_id:
              type: integer
              default: 1
            bloom_level_id:
              type: integer
              default: 2
            difficulty_level_id:
              type: integer
              default: 3
            marks:
              type: integer
              default: 1
            generation_prompt:
              type: string
            requires_diagram:
              type: boolean
              default: false
    responses:
      200:
        description: Question generated successfully
        schema:
          type: object
          properties:
            success:
              type: boolean
            data:
              type: object
            error_message:
              type: string
      400:
        description: Missing required fields
      500:
        description: Internal server error
    """
    try:
        # Get request data
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "error_message": "No request data provided",
                "data": None
            }), 400
        
        # Extract Authorization token from request headers
        auth_header = request.headers.get('Authorization', '')
        token = None
        user_id = None
        
        if auth_header:
            # Extract token (handle both "Bearer <token>" and just "<token>" formats)
            if auth_header.startswith('Bearer '):
                token = auth_header[7:]  # Remove "Bearer " prefix
            else:
                token = auth_header
            
            # Extract user ID from token
            user_id = extract_user_id_from_token(token)
            if not user_id:
                safe_print(f"Warning: Could not extract user ID from token")
        
        # Extract required fields
        generation_id = data.get('generation_id')
        subject_id = data.get('subject_id')
        topic_id = data.get('topic_id')
        stream_id_from_payload = coerce_stream_id(data.get('stream_id'))
        stream_id_from_token = extract_stream_id_from_token(token) if token else None
        effective_stream_id = stream_id_from_payload or stream_id_from_token
        section_id = data.get('section_id', 0)  # Add section_id with default 0
        question_type_id = data.get('question_type_id', 1)
        bloom_level_id = data.get('bloom_level_id', 2)
        difficulty_level_id = data.get('difficulty_level_id', 3)
        marks = data.get('marks', 1)
        generation_prompt = data.get('generation_prompt', '')
        is_aptitude, group_id = get_request_flag_and_group(data)
        # Fix: Use the correct field name from frontend
        include_diagram = data.get('requires_diagram', False)
        
        # Validate required fields
        if not all([generation_id, subject_id, topic_id]):
            return jsonify({
                "success": False,
                "error_message": "Missing required fields: generation_id, subject_id, topic_id",
                "data": None
            }), 400
        
        # Look up subject and topic names from .NET backend unified endpoints
        from services.net_backend_service import net_backend_service
        
        subject_name = None
        topic_name = None
        
        # Get subject name from .NET backend
        subject_result = net_backend_service.get_subject_by_id(
            subject_id,
            auth_token=token,
            stream_id=effective_stream_id,
            is_aptitude=is_aptitude,
            group_id=group_id
        )
        if subject_result.get('success') and subject_result.get('subject_name'):
            subject_name = subject_result['subject_name']
            safe_print(f" Retrieved subject name: {subject_name} for subject_id: {subject_id}")
        else:
            error_msg = subject_result.get('error', 'Unknown error')
            safe_print(f" ERROR: Could not retrieve subject name for subject_id: {subject_id}. Error: {error_msg}")
            # DO NOT use fallback - return error to prevent wrong data insertion
            return jsonify({
                "success": False,
                "error_message": f"Failed to retrieve subject name for subject_id {subject_id}. Cannot proceed with question generation.",
                "data": None
            }), 400
        
        # Get topic name from .NET backend
        topic_result = net_backend_service.get_topic_by_id(
            topic_id,
            subject_id,
            auth_token=token,
            is_aptitude=is_aptitude,
            group_id=group_id,
            stream_id=effective_stream_id
        )
        if topic_result.get('success') and topic_result.get('topic_name'):
            topic_name = topic_result['topic_name']
            safe_print(f" Retrieved topic name: {topic_name} for topic_id: {topic_id}")
        else:
            error_msg = topic_result.get('error', 'Unknown error')
            safe_print(f" ERROR: Could not retrieve topic name for topic_id: {topic_id}. Error: {error_msg}")
            # DO NOT use fallback - return error to prevent wrong data insertion
            return jsonify({
                "success": False,
                "error_message": f"Failed to retrieve topic name for topic_id {topic_id}. Cannot proceed with question generation.",
                "data": None
            }), 400

        topic_summary = extract_topic_summary(topic_result)

        stream_name = None
        if effective_stream_id:
            stream_result = net_backend_service.get_stream_by_id(effective_stream_id, auth_token=token)
            if stream_result.get('success') and stream_result.get('stream_name'):
                stream_name = stream_result['stream_name']
                safe_print(f" Retrieved stream name: {stream_name} for stream_id: {effective_stream_id}")
        
        # Map to our AI service format
        ai_request_data = {
            'subject_id': subject_id,
            'topic_id': topic_id,
            'stream_id': effective_stream_id,
            'subject': subject_name,  # Pass subject name to AI (required to avoid defaulting to 'Programming')
            'topic': topic_name,       # Pass topic name to AI (required to avoid defaulting to 'Programming')
            'question_type_id': question_type_id,
            'bloom_level_id': bloom_level_id,
            'difficulty_level_id': difficulty_level_id,
            'marks': marks,
            'custom_prompt': generation_prompt,  # Map generation_prompt to custom_prompt
            'requires_diagram': include_diagram,  # Map include_diagram to requires_diagram
            'requires_option_diagrams': False,
            'is_programming_question': False,
            'num_questions': 1,
            'is_aptitude': is_aptitude,
            'group_id': group_id,
            'auth_token': token
        }
        if stream_name:
            ai_request_data['stream'] = stream_name
        if topic_summary:
            ai_request_data['topic_summary'] = topic_summary
        
        # Generate question using existing AI logic
        from services.openai_service import generate_mcq_and_diagram
        ai_result = generate_mcq_and_diagram(ai_request_data)
        
        if not ai_result or 'error' in ai_result:
            error_msg = ai_result.get('error', 'Failed to generate question') if ai_result else 'No result from AI service'
            return jsonify({
                "success": False,
                "error_message": error_msg,
                "data": None
            }), 500
        
        # Handle diagram generation if required
        diagram_code = None
        diagram_image_url = None
        if include_diagram and ai_result.get('diagram_code'):
            try:
                from services.diagram_service_new import render_diagram
                image_filename = render_diagram(
                    ai_result['diagram_code'],
                    ai_result.get('library_used', 'schemdraw'),
                    app.config['UPLOAD_FOLDER']
                )
                if image_filename:
                    diagram_code = ai_result['diagram_code']
                    diagram_image_url = f"/static/images/{image_filename}"
                    safe_print(f"[OK] Diagram generated successfully: {image_filename}")
                else:
                    safe_print(f"[ERROR] Diagram generation failed for {ai_result.get('library_used', 'schemdraw')}")
            except Exception as e:
                safe_print(f"Diagram generation failed: {e}")
                diagram_code = None
                diagram_image_url = None
        
        # Prepare response data in .NET expected format
        response_data = {
            "question_text": ai_result.get('question_text', ''),
            "options": ai_result.get('options', []),
            "correct_answer": ai_result.get('correct_answer', ''),
            "explanation": ai_result.get('explanation', ''),
            "diagram_code": diagram_code,
            "diagram_image_url": diagram_image_url,  # Add diagram image URL
            "subject_id": subject_id,
            "topic_id": topic_id,
            "section_id": section_id,  # Add section_id
            "question_type_id": question_type_id,
            "bloom_level_id": bloom_level_id,
            "difficulty_level_id": difficulty_level_id,
            "marks": marks,
            "generation_prompt": generation_prompt,
            "is_aptitude": is_aptitude,
            "group_id": group_id,
            "stream_id": effective_stream_id
        }
        
        # Store question in .NET backend database
        from services.net_backend_service import net_backend_service
        
        # Add generation_id to the data for storage
        storage_data = response_data.copy()
        storage_data['generation_id'] = generation_id
        
        # Pass token, user_id, and user_type_id to store_question
        user_type_id = extract_user_type_id_from_token(token) if token else None
        storage_result = net_backend_service.store_question(
            storage_data,
            auth_token=token,
            user_id=user_id,
            user_type_id=user_type_id
        )
        
        if not storage_result['success']:
            storage_error = storage_result.get('error', 'Unknown storage error')
            safe_print(f"Warning: Failed to store question in .NET backend: {storage_error}")
            return jsonify({
                "success": False,
                "error_message": f"Question generated but storage failed: {storage_error}",
                "data": response_data
            }), 200
        else:
            # Extract jkuh and questionId from storage result and add to response data
            if storage_result.get('jkuh'):
                response_data['jkuh'] = storage_result['jkuh']
            if storage_result.get('question_id'):
                response_data['question_id'] = storage_result['question_id']
        
        return jsonify({
            "success": True,
            "error_message": None,
            "data": response_data
        }), 200
        
    except Exception as e:
        safe_print(f"Error in generate_single_question: {str(e)}")
        import traceback
        safe_print(traceback.format_exc())
        
        return jsonify({
            "success": False,
            "error_message": f"Internal server error: {str(e)}",
            "data": None
        }), 500

@app.route('/api/generation-status/<generation_id>', methods=['GET'])
@token_required
def get_generation_status(generation_id):
    """
    Get generation status from .NET backend
    ---
    tags:
      - Status & Health
    summary: Get generation status for a specific generation ID from .NET backend
    produces:
      - application/json
    parameters:
      - name: generation_id
        in: path
        type: string
        required: true
        description: Generation ID to check status
    responses:
      200:
        description: Generation status
        schema:
          type: object
          properties:
            status:
              type: string
            progress:
              type: integer
            error_message:
              type: string
            started_at:
              type: string
            completed_at:
              type: string
            question_data:
              type: object
      500:
        description: Error retrieving status
    """
    try:
        from services.net_backend_service import net_backend_service
        
        # Get status from .NET backend
        status_result = net_backend_service.get_generation_status(generation_id)
        
        if status_result['success']:
            return jsonify(status_result['status_data']), 200
        else:
            # If .NET backend is not available, return a basic status
            return jsonify({
                "status": "unknown",
                "progress": 0,
                "error_message": status_result.get('error', 'Unable to retrieve status'),
                "started_at": None,
                "completed_at": None,
                "question_data": None
            }), 200
            
    except Exception as e:
        print(f"Error in get_generation_status: {str(e)}")
        return jsonify({
            "status": "error",
            "progress": 0,
            "error_message": f"Internal server error: {str(e)}",
            "started_at": None,
            "completed_at": None,
            "question_data": None
        }), 500

if __name__ == '__main__':
    # Get host and port from environment variables or use defaults
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print(f"[START] Starting Flask server on {host}:{port}")
    print(f"[INFO] Access the application from other devices using your computer's IP address")
    # print(f" Local access: http://localhost:{port}")
    print(f"[INFO] To find your IP address, run: ipconfig (Windows) or ifconfig (Mac/Linux)")
    
    # Local dev only; production uses Waitress/systemd (see deploy/ec2/, Dockerfile)
    _debug = os.environ.get("FLASK_DEBUG", "").lower() in ("1", "true", "yes")
    app.run(host=host, port=port, debug=_debug, use_reloader=False)