import os
from flask import Flask, request, jsonify, send_from_directory
from services.openai_service import generate_mcq_and_diagram
from services.diagram_service import render_diagram
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
    
    # Call OpenAI to get question and diagram code with library selection
    result = generate_mcq_and_diagram(data)
    
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
    return jsonify(response)

if __name__ == '__main__':
    # Get host and port from environment variables or use defaults
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    print(f"🚀 Starting Flask server on {host}:{port}")
    print(f"📱 Access the application from other devices using your computer's IP address")
    print(f"🌐 Local access: http://localhost:{port}")
    print(f"📋 To find your IP address, run: ipconfig (Windows) or ifconfig (Mac/Linux)")
    
    app.run(host=host, port=port, debug=True) 