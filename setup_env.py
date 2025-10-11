#!/usr/bin/env python3
"""
Setup script to create .env file from template
"""
import os
import shutil

def setup_environment():
    """Create .env file from env.template if it doesn't exist"""
    
    if os.path.exists('.env'):
        print("[OK] .env file already exists")
        return
    
    if not os.path.exists('env.template'):
        print("[ERROR] env.template file not found")
        return
    
    try:
        shutil.copy('env.template', '.env')
        print("[OK] Created .env file from env.template")
        print("[INFO] Please edit .env file with your actual values:")
        print("   - OPENAI_API_KEY: Your OpenAI API key")
        print("   - NET_BACKEND_URL: Your .NET backend URL")
        print("   - PYTHON_BACKEND_URL: Your Python backend URL")
        print("   - Other configuration values as needed")
    except Exception as e:
        print(f"[ERROR] Error creating .env file: {e}")

if __name__ == "__main__":
    setup_environment()
