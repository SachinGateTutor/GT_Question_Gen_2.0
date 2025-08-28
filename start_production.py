#!/usr/bin/env python3
"""
Production startup script for GT Question Generator 2.0
Handles logging, error handling, and graceful shutdown
"""

import os
import sys
import logging
import signal
import time
from pathlib import Path
from waitress import serve
from app.main import app

# Configure logging
def setup_logging():
    """Setup logging configuration"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/app.log'),
            logging.FileHandler('logs/error.log', level=logging.ERROR),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Add basic health checks here
        return {'status': 'healthy', 'timestamp': time.time()}, 200
    except Exception as e:
        return {'status': 'unhealthy', 'error': str(e)}, 500

# Graceful shutdown handler
def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    logger = logging.getLogger(__name__)
    logger.info(f"Received signal {signum}. Shutting down gracefully...")
    sys.exit(0)

def main():
    """Main production startup function"""
    # Setup logging
    logger = setup_logging()
    logger.info("Starting GT Question Generator 2.0 in production mode...")
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Get configuration from environment
    host = os.environ.get('FLASK_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_PORT', 5000))
    
    # Validate environment
    required_env_vars = ['OPENAI_API_KEY', 'DB_SERVER', 'DB_NAME', 'DB_USER', 'DB_PASSWORD']
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        sys.exit(1)
    
    logger.info(f"Configuration loaded - Host: {host}, Port: {port}")
    logger.info("Starting Waitress server...")
    
    try:
        # Start Waitress server
        serve(app, host=host, port=port, threads=4)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 