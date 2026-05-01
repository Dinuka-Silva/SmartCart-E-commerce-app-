#!/bin/bash

echo "Starting LuxIQ ML Service..."

# Create necessary directories
mkdir -p models logs

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python3 is not installed. Please install Python3 first."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Download NLTK data
echo "Downloading NLTK data..."
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('wordnet')"

# Download spaCy model
echo "Downloading spaCy model..."
python -m spacy download en_core_web_sm

# Start the service
echo "Starting ML service on port 8000..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
