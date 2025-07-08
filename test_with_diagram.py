import urllib.request
import json

# Test data with diagram requirement
data = {
    "stream": "CS",
    "subject": "Digital Logic", 
    "topic": "Logic Gates",
    "question_type": "MCQ",
    "requires_diagram": True,
    "custom_prompt": "Generate a question about AND gates and include a simple AND gate diagram using schemdraw. Make sure to use valid schemdraw syntax."
}

# Convert to JSON
json_data = json.dumps(data).encode('utf-8')

# Create request
req = urllib.request.Request(
    'http://127.0.0.1:5000/api/generate',
    data=json_data,
    headers={'Content-Type': 'application/json'}
)

try:
    print("Sending request to Flask server...")
    # Send request
    with urllib.request.urlopen(req) as response:
        print(f"Got response with status: {response.status}")
        result = json.loads(response.read().decode('utf-8'))
        print("Status Code:", response.status)
        print("Response:")
        print(json.dumps(result, indent=2))
        
        # Check if we got real AI response or sample data
        if result.get('question_text') == 'Sample question for testing':
            print("\n⚠️  Still getting sample data. Check if OpenAI API key is loaded correctly.")
        else:
            print("\n✅ Got real AI-generated response!")
            
        if result.get('diagram_code'):
            print("✅ Diagram code generated!")
        if result.get('diagram_image_url'):
            print("✅ Diagram image saved!")
            
except Exception as e:
    print(f"Error: {e}") 