#!/usr/bin/env python3
"""
Network Setup Script for AI MCQ Generator
This script helps you configure the application for network access.
"""

import socket
import subprocess
import platform
import os
import re

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

def update_config_file(ip_address):
    """Update the config.js file with the IP address"""
    config_content = f'''// Configuration file for AI MCQ Generator
// Change the API_URL to your computer's IP address for network access

const config = {{
    // For local development (same computer)
    // API_URL: 'http://127.0.0.1:5000/api/generate',
    
    // For network access (replace with your computer's IP address)
    // Example: API_URL: 'http://192.168.1.100:5000/api/generate',
    API_URL: 'http://{ip_address}:5000/api/generate',
    
    // Flask server settings
    FLASK_HOST: '0.0.0.0',
    FLASK_PORT: 5000
}};

// Instructions:
// 1. Find your computer's IP address:
//    - Windows: Run 'ipconfig' in command prompt
//    - Mac/Linux: Run 'ifconfig' in terminal
// 2. Replace the IP address in API_URL above
// 3. Make sure your firewall allows connections on port 5000
// 4. Start the Flask server: python app/main.py
// 5. Access from other devices: http://YOUR_IP:5000
'''
    
    try:
        with open('config.js', 'w') as f:
            f.write(config_content)
        return True
    except Exception as e:
        print(f"Error updating config.js: {e}")
        return False

def main():
    print("🌐 AI MCQ Generator - Network Setup")
    print("=" * 50)
    
    # Try to get IP address
    ip_address = get_local_ip()
    if not ip_address:
        ip_address = get_ip_from_command()
    
    if ip_address:
        print(f"✅ Found your IP address: {ip_address}")
        print(f"📱 Other devices can access the app at: http://{ip_address}:5000")
        
        # Update config file
        if update_config_file(ip_address):
            print("✅ Updated config.js with your IP address")
        else:
            print("❌ Failed to update config.js")
    else:
        print("❌ Could not automatically detect your IP address")
        print("📋 Please run 'ipconfig' (Windows) or 'ifconfig' (Mac/Linux) to find your IP")
        print("🔧 Then manually update the API_URL in config.js")
    
    print("\n📋 Next Steps:")
    print("1. Start the Flask server: python app/main.py")
    print("2. Open index.html in your browser")
    print("3. From other devices, open: http://YOUR_IP:5000")
    print("4. Make sure your firewall allows connections on port 5000")
    
    print("\n🔧 Manual Configuration:")
    print("If automatic detection failed, edit config.js and change:")
    print("API_URL: 'http://YOUR_IP_ADDRESS:5000/api/generate'")

if __name__ == "__main__":
    main() 