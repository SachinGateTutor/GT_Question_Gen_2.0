# Environment Setup Guide

This guide explains how to set up environment variables for the GT Question Generator 2.0.

## Quick Setup

1. **Copy the environment template:**
   ```bash
   cp env.template .env
   ```

2. **Edit the .env file with your actual values:**
   ```bash
   # Required: OpenAI API Key
   OPENAI_API_KEY=your_actual_openai_api_key_here
   
   # Backend URLs (adjust as needed)
   NET_BACKEND_URL=http://192.168.0.102:5125
   PYTHON_BACKEND_URL=http://192.168.0.101:5000
   ```

## Environment Variables

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | `sk-...` |

### Optional Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NET_BACKEND_URL` | .NET backend service URL | `http://192.168.0.102:5125` |
| `PYTHON_BACKEND_URL` | Python backend service URL | `http://192.168.0.101:5000` |
| `FLASK_HOST` | Flask server host | `0.0.0.0` |
| `FLASK_PORT` | Flask server port | `5000` |
| `FLASK_ENV` | Flask environment | `production` |
| `SECRET_KEY` | Flask secret key | `your_secret_key_here` |

## Security Notes

- **Never commit .env files to version control**
- The .env file is already in .gitignore
- Keep your API keys secure and private
- Use different API keys for development and production

## Troubleshooting

### "OPENAI_API_KEY not found" Error
- Make sure you have created a .env file
- Verify the OPENAI_API_KEY is set correctly
- Check that the .env file is in the project root directory

### Backend Connection Issues
- Verify NET_BACKEND_URL and PYTHON_BACKEND_URL are correct
- Ensure the backend services are running
- Check network connectivity between services

## Automated Setup

You can use the provided setup script:

```bash
python setup_env.py
```

This will automatically create a .env file from the template if one doesn't exist.

