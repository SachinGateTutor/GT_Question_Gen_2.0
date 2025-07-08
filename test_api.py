import requests
import json

# Test the API endpoint
url = "http://127.0.0.1:5000/api/generate"

# Sample test data
test_data = {
    "stream": "CS",
    "subject": "Digital Logic",
    "topic": "AND Gate",
    "question_type": "MCQ",
    "requires_diagram": True,
    "custom_prompt": "Focus on basic logic gate operation."
}

try:
    response = requests.post(url, json=test_data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except requests.exceptions.ConnectionError:
    print("Error: Could not connect to the server. Make sure the Flask app is running.")
except Exception as e:
    print(f"Error: {e}") 