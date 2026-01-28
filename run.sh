#!/bin/bash

# Create necessary directories
mkdir -p docs 

# Check if backend directory exists
if [ ! -d "backend" ]; then
    echo "Error: backend directory not found"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv-new" ]; then
    echo "Error: Virtual environment not found. Please run: python -m venv .venv-new"
    exit 1
fi

echo "Starting Course Materials RAG System..."
echo "Make sure you have set your ANTHROPIC_API_KEY in .env"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Warning: .env file not found. Copy .env.example to .env and add your API key."
fi

# Start the server from backend directory
echo "Starting uvicorn server on http://127.0.0.1:8000"
cd backend && ../.venv-new/Scripts/python.exe -m uvicorn app:app --reload --port 8000