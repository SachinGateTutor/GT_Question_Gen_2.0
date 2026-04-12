# AI MCQ Generator with Dynamic Diagram Support

An intelligent Multiple Choice Question (MCQ) generator powered by OpenAI that automatically selects the best visualization library for different subjects and topics.

## Features

### Dynamic Library Selection
The system intelligently chooses the most appropriate diagram library based on the subject and topic:

- **schemdraw** - Electronic circuits, logic gates, simple block diagrams
- **matplotlib** - Mathematical plots, charts, graphs, 2D visualizations  
- **networkx** - Network graphs, social networks, relationship diagrams
- **graphviz** - Flowcharts, process diagrams, hierarchical structures
- **plotly** - Interactive charts, 3D plots, statistical visualizations
- **seaborn** - Statistical plots, data visualizations
- **pillow** - Image manipulation, simple geometric shapes
- **turtle** - Simple geometric drawings, educational diagrams

### Two-Stage AI Processing
1. **Stage 1**: AI analyzes the subject/topic and selects the best library
2. **Stage 2**: AI generates question and diagram code using the selected library

### Subject-Specific Diagrams
- **Microprocessor/Electronics**: Circuit diagrams with schemdraw
- **Mathematics**: Mathematical plots with matplotlib
- **Computer Networks**: Network graphs with networkx
- **Software Engineering**: Flowcharts with graphviz
- **Statistics**: Statistical plots with seaborn
- **And many more...**

## Quick Start

### Prerequisites
- Python **3.13+** (same version as production / Docker)
- OpenAI API key

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd GT_Question_Gen_2.0
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up your OpenAI API key**
   - Copy `env.template` to `.env` in the project root
   - Set `OPENAI_API_KEY` (and `NET_BACKEND_URL` if you use the .NET API)

4. **Run the application** (development; optional: `export FLASK_DEBUG=1` on Linux/Mac or `set FLASK_DEBUG=1` on Windows for Flask debug mode)
```bash
cd app
python main.py
```

5. **Open the frontend**
   - Open `index.html` in your browser
   - Or navigate to `http://localhost:5000` if you set up Flask serving

## Usage

### Web Interface
1. Select your stream (CS, IT, ECE)
2. Enter the subject (e.g., "Digital Electronics", "Mathematics")
3. Enter the topic (e.g., "Logic Gates", "Calculus")
4. Choose question type (MCQ)
5. Check "Include Diagram" for visual questions
6. Click "Generate Question"

### API Usage
```python
import requests

data = {
    "stream": "CS",
    "subject": "Digital Electronics", 
    "topic": "Logic Gates",
    "question_type": "MCQ",
    "requires_diagram": True
}

response = requests.post("http://localhost:5000/api/generate", json=data)
result = response.json()

print(f"Question: {result['question_text']}")
print(f"Library Used: {result['library_used']}")
print(f"Diagram URL: {result['diagram_image_url']}")
```

## Project Structure

```
GT_Question_Gen_2.0/
├── app/
│   ├── main.py                 # Flask application
│   ├── services/
│   │   ├── openai_service.py   # OpenAI integration with dynamic library selection
│   │   └── diagram_service.py  # Multi-library diagram rendering
│   └── static/
│       └── images/             # Generated diagram images
├── index.html                  # Web frontend
├── requirements.txt            # Python dependencies
└── README.md                  # This file
```

## Configuration

### Supported Libraries

| Library | Best For | Example Subjects |
|---------|----------|------------------|
| **schemdraw** | Electronic circuits, logic gates | Digital Electronics, Microprocessor |
| **matplotlib** | Mathematical plots, charts | Physics, Mathematics, Statistics |
| **networkx** | Network graphs, relationships | Social Networks, Computer Networks |
| **graphviz** | Flowcharts, process diagrams | Software Engineering, Business Processes |
| **plotly** | Interactive charts, 3D plots | Data Science, Advanced Statistics |
| **seaborn** | Statistical plots, data viz | Statistics, Research Data |
| **pillow** | Simple geometric shapes | Basic Geometry, Simple Diagrams |
| **turtle** | Educational drawings | Programming Education, Simple Graphics |

### Customization

You can customize the library selection by modifying the prompts in `app/services/openai_service.py`:

```python
def get_library_specific_prompt(library_name):
    # Add your custom prompts here
    pass

def get_library_rules(library_name):
    # Add your custom rules here
    pass
```

## Testing

Run the test script to verify the dynamic library selection:

```bash
python test_dynamic_libraries.py
```

This will test library selection for various subjects and topics.

## How It Works

### 1. Library Selection
When a user requests a diagram, the system:
- Analyzes the subject and topic
- Considers the strengths of each available library
- Selects the most appropriate library using AI

### 2. Code Generation
The AI generates:
- A relevant MCQ question
- Python code using the selected library
- Proper error handling and fallbacks

### 3. Diagram Rendering
The backend:
- Executes the generated code safely
- Renders the diagram using the selected library
- Saves the image to the static folder
- Returns the image URL

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   - Check your API key in `app/services/openai_service.py`
   - Ensure you have sufficient API credits

2. **Diagram Generation Fails**
   - The system automatically falls back to schemdraw
   - Check the console for detailed error messages

3. **Missing Dependencies**
   - Run `pip install -r requirements.txt`
   - Some libraries may require system dependencies (e.g., graphviz)

### Debug Mode
Enable debug prints by checking the console output for:
- Selected library information
- Raw OpenAI responses
- Diagram generation logs

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add your improvements
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Acknowledgments

- OpenAI for providing the GPT models
- The Python community for the excellent visualization libraries
- All contributors to this project

---

**Made with care by PragyaAI**