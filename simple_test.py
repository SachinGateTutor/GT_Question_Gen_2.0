import urllib.request
import json

# Test data
data = {
    "stream": "CS",
    "subject": "Digital Logic", 
    "topic": "AND Gate",
    "question_type": "MCQ",
    "requires_diagram": True,
    "custom_prompt": "Focus on basic logic gate operation."
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
    # Send request
    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        print("Status Code:", response.status)
        print("Response:")
        print(json.dumps(result, indent=2))
except Exception as e:
    print(f"Error: {e}") 