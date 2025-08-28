# 🌐 Network Setup Guide for AI MCQ Generator

This guide will help you set up the AI MCQ Generator to be accessible from other devices on your WiFi network.

## 🚀 Quick Start

### Option 1: Automatic Setup (Recommended)

**Windows:**
```bash
start_server.bat
```

**Mac/Linux:**
```bash
./start_server.sh
```

### Option 2: Manual Setup

1. **Find your IP address:**
   - **Windows:** Open Command Prompt and run `ipconfig`
   - **Mac/Linux:** Open Terminal and run `ifconfig`
   - Look for your local IP address (usually starts with 192.168.x.x or 10.0.x.x)

2. **Configure the application:**
   ```bash
   python setup_network.py
   ```

3. **Start the server:**
   ```bash
   cd app
   python main.py
   ```

## 📱 Accessing from Other Devices

Once the server is running, other devices on your network can access the application at:
```
http://YOUR_IP_ADDRESS:5000
```

For example: `http://192.168.1.100:5000`

## 🔧 Manual Configuration

If automatic setup doesn't work, you can manually configure the application:

1. **Edit `config.js`:**
   ```javascript
   API_URL: 'http://YOUR_IP_ADDRESS:5000/api/generate'
   ```

2. **Start the server:**
   ```bash
   cd app
   python main.py
   ```

## 🛡️ Firewall Configuration

### Windows Firewall
1. Open Windows Defender Firewall
2. Click "Allow an app or feature through Windows Defender Firewall"
3. Click "Change settings"
4. Click "Allow another app"
5. Browse to your Python executable
6. Make sure both Private and Public are checked

### Mac Firewall
1. Go to System Preferences > Security & Privacy > Firewall
2. Click "Firewall Options"
3. Click "+" to add an application
4. Select Python or Terminal
5. Set to "Allow incoming connections"

### Linux Firewall
```bash
sudo ufw allow 5000
```

## 🔍 Troubleshooting

### "Connection Refused" Error
- Make sure the Flask server is running
- Check if port 5000 is not used by another application
- Verify firewall settings

### "Cannot Access from Other Devices"
- Ensure all devices are on the same WiFi network
- Check if your router blocks local network communication
- Try using a different port (edit `app/main.py`)

### "IP Address Not Found"
- Run the setup script manually: `python setup_network.py`
- Check your network connection
- Try restarting your WiFi router

## 📋 Testing Network Access

1. **From the host computer:**
   - Open `http://localhost:5000` in your browser

2. **From other devices:**
   - Open `http://YOUR_IP:5000` in their browsers
   - Make sure they're connected to the same WiFi network

## 🔄 Changing Port

If port 5000 is already in use, you can change it:

1. **Set environment variable:**
   ```bash
   # Windows
   set FLASK_PORT=8080
   
   # Mac/Linux
   export FLASK_PORT=8080
   ```

2. **Or edit `app/main.py`:**
   ```python
   port = int(os.environ.get('FLASK_PORT', 8080))
   ```

3. **Update `config.js`:**
   ```javascript
   API_URL: 'http://YOUR_IP:8080/api/generate'
   ```

## 📊 Network Requirements

- **Bandwidth:** Minimal (text-based API calls)
- **Latency:** Low latency preferred for responsive UI
- **Security:** Basic HTTP (consider HTTPS for production)
- **Ports:** 5000 (configurable)

## 🎯 Use Cases

- **Classroom Testing:** Students can access from their devices
- **Mobile Testing:** Test on phones and tablets
- **Remote Access:** Access from different rooms
- **Collaboration:** Multiple users can generate questions simultaneously

## 🔒 Security Notes

⚠️ **Important:** This setup is for local network use only. For production deployment:
- Use HTTPS
- Implement proper authentication
- Configure a production web server (nginx, Apache)
- Use environment variables for sensitive data

---

**Need help?** Check the main README.md for more information about the application. 