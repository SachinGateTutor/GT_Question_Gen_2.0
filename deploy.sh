#!/bin/bash

# GT Question Generator 2.0 - Quick Deployment Script
# This script sets up the application on a Linux server

set -e

echo "🚀 GT Question Generator 2.0 - Deployment Script"
echo "=================================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run as root (use sudo)"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
apt-get update
apt-get upgrade -y

# Install required packages
echo "🔧 Installing required packages..."
apt-get install -y python3 python3-pip python3-venv git curl wget graphviz nginx

# Create application user
echo "👤 Creating application user..."
useradd -m -s /bin/bash gt-generator || true
usermod -aG sudo gt-generator

# Create application directory
echo "📁 Setting up application directory..."
mkdir -p /opt/gt-question-generator
chown gt-generator:gt-generator /opt/gt-question-generator

# Clone repository (if not already present)
if [ ! -d "/opt/gt-question-generator/.git" ]; then
    echo "📥 Cloning repository..."
    su - gt-generator -c "git clone https://github.com/SachinGateTutor/GT_Question_Gen_2.0.git /opt/gt-question-generator"
else
    echo "📥 Updating repository..."
    su - gt-generator -c "cd /opt/gt-question-generator && git pull"
fi

# Set up Python environment
echo "🐍 Setting up Python environment..."
su - gt-generator -c "cd /opt/gt-question-generator && python3 -m venv venv"
su - gt-generator -c "cd /opt/gt-question-generator && source venv/bin/activate && pip install -r requirements.txt"

# Create necessary directories
echo "📂 Creating directories..."
mkdir -p /opt/gt-question-generator/logs
mkdir -p /opt/gt-question-generator/app/static/images
chown -R gt-generator:gt-generator /opt/gt-question-generator

# Install systemd service
echo "⚙️ Installing systemd service..."
cp /opt/gt-question-generator/gt-question-generator.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable gt-question-generator.service

# Configure firewall
echo "🔥 Configuring firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 5000/tcp
ufw --force enable

# Configure Nginx (optional)
echo "🌐 Configuring Nginx..."
cat > /etc/nginx/sites-available/gt-generator << 'EOF'
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

ln -sf /etc/nginx/sites-available/gt-generator /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
systemctl restart nginx

echo "✅ Deployment completed!"
echo ""
echo "📋 Next steps:"
echo "1. Set up your environment variables in /opt/gt-question-generator/.env"
echo "2. Configure your database connection"
echo "3. Start the service: systemctl start gt-question-generator"
echo "4. Check status: systemctl status gt-question-generator"
echo "5. View logs: journalctl -u gt-question-generator -f"
echo ""
echo "🌐 Application will be available at: http://your-server-ip"
echo "📊 Health check: http://your-server-ip/health" 