#!/usr/bin/env python3
"""
Network Setup Script for GT Question Generator 2.0
This script configures the hybrid Python + .NET backend architecture for network access.
"""

import socket
import subprocess
import platform
import os
import re
import requests
import time

def get_local_ip():
    """Get the local IP address of this computer"""
    try:
        # Create a socket to get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return None

def get_ip_from_command():
    """Get IP address using system commands"""
    try:
        if platform.system() == "Windows":
            result = subprocess.run(['ipconfig'], capture_output=True, text=True)
            # Look for IPv4 address
            for line in result.stdout.split('\n'):
                if 'IPv4 Address' in line:
                    match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        return match.group(1)
        else:
            result = subprocess.run(['ifconfig'], capture_output=True, text=True)
            # Look for inet address
            for line in result.stdout.split('\n'):
                if 'inet ' in line and not line.strip().startswith('127.'):
                    match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', line)
                    if match:
                        return match.group(1)
    except Exception:
        pass
    return None

def check_service_health(ip_address, port, service_name):
    """Check if a service is running and accessible"""
    try:
        url = f"http://{ip_address}:{port}"
        if service_name == "Python Flask":
            url += "/api/health"
        elif service_name == ".NET Backend":
            url += "/api/question-master/ai-service-status"
        
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def update_config_file(ip_address):
    """Update the config.js file with the correct hybrid architecture configuration"""
    config_content = f'''// Configuration file for GT Question Generator 2.0
// Hybrid Architecture: Python Flask + .NET Backend
// Updated for network access

const config = {{
    // .NET Backend API - for data fetching and storage
    NET_BACKEND_URL: 'http://{ip_address}:5125',
    
    // .NET Backend endpoints - for data fetching
    NET_STATUS_ENDPOINT: 'http://{ip_address}:5125/api/question-master/generation-status',
    NET_QUESTIONS_ENDPOINT: 'http://{ip_address}:5125/api/QuestionRetrieval/filter',
    NET_AI_QUESTIONS_ENDPOINT: 'http://{ip_address}:5125/api/QuestionRetrieval/filter?IsAIGenerated=true',
    NET_QUESTION_BY_ID_ENDPOINT: 'http://{ip_address}:5125/api/QuestionRetrieval',
    NET_HEALTH_ENDPOINT: 'http://{ip_address}:5125/api/question-master/ai-service-status',
    
    // .NET Backend reference data endpoints
    NET_COURSES_ENDPOINT: 'http://{ip_address}:5125/api/CoursesNew/get',
    NET_STREAMS_ENDPOINT: 'http://{ip_address}:5125/api/Stream',
    NET_SUBJECTS_ENDPOINT: 'http://{ip_address}:5125/api/SubjectNew',
    NET_TOPICS_ENDPOINT: 'http://{ip_address}:5125/api/Topic/get',
    NET_QUESTION_TYPES_ENDPOINT: 'http://{ip_address}:5125/api/Types/question',
    NET_DIFFICULTY_LEVELS_ENDPOINT: 'http://{ip_address}:5125/api/DifficultyLevel',
    NET_BLOOM_LEVELS_ENDPOINT: 'http://{ip_address}:5125/api/BloomLevel',
    
    // Python service - for AI question generation and diagram rendering
    NET_GENERATE_ENDPOINT: 'http://{ip_address}:5000/api/generate-question',
    
    // Legacy API_URL for backward compatibility (now points to Python service)
    API_URL: 'http://{ip_address}:5000/api/generate-question',
    
    // Python service (fallback only)
    PYTHON_BASE_URL: 'http://{ip_address}:5000',
    PYTHON_API_URL: 'http://{ip_address}:5000/api/generate',
    
    // Flask server settings (for local development)
    FLASK_HOST: '0.0.0.0',   
    FLASK_PORT: 5000
}};

// Instructions for Hybrid Architecture:
// 1. .NET Backend (port 5125): Handles data management, storage, and retrieval
// 2. Python Flask (port 5000): Handles AI processing, diagram generation
// 3. Both services must be running for full functionality
// 4. Frontend served by Python Flask on port 5000
// 5. Make sure firewall allows connections on ports 5000 and 5125
'''
    
    try:
        with open('config.js', 'w') as f:
            f.write(config_content)
        return True
    except Exception as e:
        print(f"Error updating config.js: {e}")
        return False

def main():
    print("🌐 GT Question Generator 2.0 - Hybrid Network Setup")
    print("=" * 60)
    print("Architecture: Python Flask + .NET Backend")
    print("=" * 60)
    
    # Try to get IP address
    ip_address = get_local_ip()
    if not ip_address:
        ip_address = get_ip_from_command()
    
    if ip_address:
        print(f"✅ Found your IP address: {ip_address}")
        print(f"📱 Other devices can access the app at: http://{ip_address}:5000")
        
        # Check service health
        print("\n🔍 Checking service availability...")
        python_healthy = check_service_health(ip_address, 5000, "Python Flask")
        dotnet_healthy = check_service_health(ip_address, 5125, ".NET Backend")
        
        print(f"🐍 Python Flask (port 5000): {'✅ Running' if python_healthy else '❌ Not accessible'}")
        print(f"🔷 .NET Backend (port 5125): {'✅ Running' if dotnet_healthy else '❌ Not accessible'}")
        
        if not python_healthy:
            print("⚠️  Python Flask service not running. Start with: python app/main.py")
        if not dotnet_healthy:
            print("⚠️  .NET Backend service not running. Start your .NET backend service.")
        
        # Update config file
        if update_config_file(ip_address):
            print("✅ Updated config.js with hybrid architecture configuration")
        else:
            print("❌ Failed to update config.js")
    else:
        print("❌ Could not automatically detect your IP address")
        print("📋 Please run 'ipconfig' (Windows) or 'ifconfig' (Mac/Linux) to find your IP")
        print("🔧 Then manually update the IP addresses in config.js")
    
    print("\n📋 Next Steps for Hybrid Architecture:")
    print("1. Start .NET Backend service (port 5125)")
    print("2. Start Python Flask service: python app/main.py (port 5000)")
    print("3. Open index.html in your browser")
    print("4. From other devices, open: http://YOUR_IP:5000")
    print("5. Make sure firewall allows connections on ports 5000 and 5125")
    
    print("\n🔧 Manual Configuration:")
    print("If automatic detection failed, edit config.js and update:")
    print("- NET_BACKEND_URL: 'http://YOUR_IP:5125'")
    print("- NET_GENERATE_ENDPOINT: 'http://YOUR_IP:5000/api/generate-question'")
    
    print("\n🏗️ Architecture Overview:")
    print("Frontend (HTML/JS) → Python Flask (AI Processing) → .NET Backend (Data Storage)")
    print("                    ↓")
    print("              Diagram Generation & Static Files")

if __name__ == "__main__":
    main() 