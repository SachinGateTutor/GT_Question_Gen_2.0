# 🚀 GT Question Generator 2.0 - Deployment Guide

## Overview
This guide will help you deploy the AI-powered MCQ generator on a different machine with higher specs and network connectivity.

## 📋 Prerequisites

### System Requirements
- **OS**: Windows Server 2019/2022, Ubuntu 20.04+, or CentOS 8+
- **RAM**: Minimum 8GB, Recommended 16GB+
- **Storage**: 50GB+ free space
- **CPU**: 4+ cores recommended
- **Network**: Stable internet connection for OpenAI API calls

### Software Requirements
- **Python**: 3.8+ (3.11+ recommended)
- **SQL Server**: 2019+ (Express or Standard)
- **Git**: Latest version
- **Node.js**: 16+ (for npm if needed)

## 🔧 Installation Steps

### 1. Clone the Repository
```bash
git clone https://github.com/SachinGateTutor/GT_Question_Gen_2.0.git
cd GT_Question_Gen_2.0
```

### 2. Set Up Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup

#### Option A: SQL Server Express (Free)
1. Download SQL Server Express from Microsoft
2. Install with default settings
3. Enable TCP/IP protocol in SQL Server Configuration Manager
4. Create a new database named `GTQuestionDB`

#### Option B: SQL Server Standard/Enterprise
1. Install SQL Server with your license
2. Create database `GTQuestionDB`
3. Configure network access

#### Database Schema Setup
```sql
-- Run these scripts in SQL Server Management Studio
-- 1. Create database
CREATE DATABASE GTQuestionDB;
GO

USE GTQuestionDB;
GO

-- 2. Create tables (run the SQL scripts from the project)
-- The exact schema will be provided in separate SQL files
```

### 4. Environment Configuration

#### Create Environment File
Create `config.env` file:
```env
# Database Configuration
DB_SERVER=localhost
DB_NAME=GTQuestionDB
DB_USER=your_username
DB_PASSWORD=your_password

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# Flask Configuration
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_ENV=production

# Security
SECRET_KEY=your_secret_key_here
```

### 5. API Key Setup
1. Get OpenAI API key from https://platform.openai.com/
2. Add it to `config.env` file
3. Ensure sufficient credits for API calls

## 🚀 Running the Application

### Development Mode
```bash
# Activate virtual environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Run Flask app
python app/main.py
```

### Production Mode (Recommended)

#### Option A: Using Gunicorn (Linux)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app.main:app
```

#### Option B: Using Waitress (Windows)
```bash
pip install waitress
waitress-serve --host=0.0.0.0 --port=5000 app.main:app
```

#### Option C: Using Docker
```bash
# Build Docker image
docker build -t gt-question-generator .

# Run container
docker run -d -p 5000:5000 --name gt-generator gt-question-generator
```

## 🌐 Network Configuration

### Firewall Setup
- **Windows**: Allow port 5000 in Windows Firewall
- **Linux**: `sudo ufw allow 5000`
- **Router**: Forward port 5000 to your server IP

### Domain/SSL Setup (Optional)
1. Purchase domain name
2. Set up SSL certificate (Let's Encrypt)
3. Configure reverse proxy (Nginx/Apache)

## 📊 Monitoring & Maintenance

### Logs
- Application logs: `logs/app.log`
- Error logs: `logs/error.log`
- Access logs: `logs/access.log`

### Health Checks
- Application: `http://your-server:5000/health`
- Database: `http://your-server:5000/api/health`

### Backup Strategy
1. **Database**: Daily SQL Server backups
2. **Application**: Git repository backup
3. **Generated Images**: Regular backup of `app/static/images/`

## 🔒 Security Considerations

### Network Security
- Use HTTPS in production
- Implement rate limiting
- Set up proper firewall rules
- Regular security updates

### Database Security
- Use strong passwords
- Limit database user permissions
- Regular security patches
- Encrypt sensitive data

### API Security
- Rotate API keys regularly
- Monitor API usage
- Implement request throttling
- Log all API calls

## 📈 Performance Optimization

### For High Traffic
1. **Load Balancing**: Use multiple instances
2. **Caching**: Implement Redis for caching
3. **CDN**: Use CDN for static files
4. **Database**: Optimize queries and indexes

### Monitoring Tools
- **Application**: New Relic, DataDog
- **Server**: Nagios, Zabbix
- **Database**: SQL Server Profiler

## 🆘 Troubleshooting

### Common Issues
1. **Port 5000 in use**: Change port in config
2. **Database connection failed**: Check credentials and firewall
3. **OpenAI API errors**: Check API key and credits
4. **Memory issues**: Increase RAM or optimize code

### Support
- Check logs in `logs/` directory
- Monitor system resources
- Test API endpoints individually
- Verify network connectivity

## 📝 Maintenance Schedule

### Daily
- Check application logs
- Monitor API usage
- Verify database connectivity

### Weekly
- Update dependencies
- Backup database
- Review performance metrics

### Monthly
- Security updates
- Performance optimization
- Capacity planning

## 🔄 Updates & Deployment

### Code Updates
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Restart application
# (Use your deployment method)
```

### Database Updates
- Backup before updates
- Test in staging environment
- Use migration scripts
- Monitor during deployment

---

## 📞 Support
For technical support or questions:
- Check the logs first
- Review this deployment guide
- Contact the development team
- Check GitHub issues

**Last Updated**: July 2025
**Version**: 2.0 