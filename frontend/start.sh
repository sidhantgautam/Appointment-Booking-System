#!/bin/bash

# Voice AI Clinic Frontend Startup Script

echo "🚀 Starting Voice AI Clinic Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ and try again."
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Node.js version 16+ is required. Current version: $(node -v)"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm and try again."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from example..."
    cp .env.example .env
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    npm install
    
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies"
        exit 1
    fi
fi

# Check if backend is running
echo "🔍 Checking backend connection..."
BACKEND_URL=${REACT_APP_API_URL:-"http://localhost:8000"}

if curl -s "$BACKEND_URL" > /dev/null; then
    echo "✅ Backend is running at $BACKEND_URL"
else
    echo "⚠️  Warning: Backend not responding at $BACKEND_URL"
    echo "   Make sure the backend server is running before using the app"
fi

# Start the development server
echo "🌐 Starting development server..."
echo "   Frontend will be available at: http://localhost:3000"
echo "   Backend should be running at: $BACKEND_URL"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm start