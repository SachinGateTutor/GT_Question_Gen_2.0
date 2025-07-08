import openai

# Test the API key directly
api_key = "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"

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