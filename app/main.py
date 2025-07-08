import os
from flask import Flask, request, jsonify
from services.openai_service import generate_mcq_and_diagram
from services.diagram_service import render_schemdraw_diagram
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'images')

@app.route('/api/generate', methods=['POST'])
def generate():
    data = request.get_json()
    # Call OpenAI to get question and diagram code
    result = generate_mcq_and_diagram(data)
    image_url = None
    if result.get('diagram_code'):
        image_filename = render_schemdraw_diagram(result['diagram_code'], app.config['UPLOAD_FOLDER'])
        if image_filename:
            image_url = f"/static/images/{image_filename}"
    response = {
        'question_text': result.get('question_text'),
        'options': result.get('options'),
        'correct_answer': result.get('correct_answer'),
        'explanation': result.get('explanation'),
        'diagram_code': result.get('diagram_code'),
        'diagram_image_url': image_url
    }
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True) 