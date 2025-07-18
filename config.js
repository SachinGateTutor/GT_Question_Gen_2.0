// Configuration file for AI MCQ Generator
// Change the API_URL to your computer's IP address for network access

const config = {
    // For local development (same computer)
    // API_URL: 'http://127.0.0.1:5000/api/generate',
    
    // For network access (replace with your computer's IP address)
    // Example: API_URL: 'http://192.168.1.100:5000/api/generate',
    API_URL: 'http://192.168.0.120:5000/api/generate', // personal system
    // API_URL: 'http://192.168.0.119:5000/api/generate', // main system
    
    // Flask server settings
    FLASK_HOST: '0.0.0.0',   
    FLASK_PORT: 5000
};

// Instructions:
// 1. Find your computer's IP address:
//    - Windows: Run 'ipconfig' in command prompt
//    - Mac/Linux: Run 'ifconfig' in terminal
// 2. Replace the IP address in API_URL above
// 3. Make sure your firewall allows connections on port 5000
// 4. Start the Flask server: python app/main.py
// 5. Access from other devices: http://YOUR_IP:5000
