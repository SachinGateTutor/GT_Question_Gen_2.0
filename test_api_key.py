import os
import openai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
print(f"API Key loaded: {api_key[:20] if api_key else 'None'}...")

if not api_key or api_key == 'your_openai_api_key_here':
    print("❌ API key not set or is placeholder")
    exit(1)

try:
    client = openai.OpenAI(api_key=api_key)
    print("✅ OpenAI client created successfully")
    
    # Test a simple API call
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=10
    )
    print("✅ API call successful!")
    print(f"Response: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"❌ API call failed: {e}") 