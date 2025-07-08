import os
from flask import Flask, request, jsonify
from services.openai_service import generate_mcq_and_diagram
from services.diagram_service import render_diagram
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'images')

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
    app.run(debug=True) 