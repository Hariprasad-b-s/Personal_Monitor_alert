#!/bin/bash

# Daily Activity Tracker - Start Script

echo "🎯 Starting Daily Activity Tracker..."
echo ""

# Activate virtual environment
source venv/bin/activate

# Check if dependencies are installed
if ! python -c "import flask" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the Flask application
echo "🚀 Launching application on http://localhost:5001"
echo "Press CTRL+C to stop the server"
echo ""

python app.py
