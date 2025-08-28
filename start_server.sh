#!/bin/bash

echo "🌐 AI MCQ Generator - Network Server"
echo "===================================="

echo ""
echo "📋 Setting up network access..."
python3 setup_network.py

echo ""
echo "🚀 Starting Flask server..."
echo "📱 The server will be accessible from other devices on your network"
echo "🌐 Local access: http://localhost:5000"
echo ""

cd app
python3 main.py 