#!/bin/bash

# LifeLink Setup Script
echo "🏥 LifeLink Setup - Emergency Coordination System"
echo "================================================"
echo

# Check Python version
python_version=$(python3 --version 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ Python found: $python_version"
else
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

# Check Node.js version
node_version=$(node --version 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "✅ Node.js found: $node_version"
else
    echo "❌ Node.js not found. Please install Node.js 18+"
    exit 1
fi

echo

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
pip install -r api_requirements.txt

echo

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo

# Check for .env file
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "📝 Please edit .env file with your API keys:"
    echo "   - GROQ_API_KEY (get from https://console.groq.com/keys)"
    echo "   - TWILIO credentials (optional, for WhatsApp)"
else
    echo "✅ .env file already exists"
fi

echo
echo "🎉 Setup complete!"
echo
echo "🚀 To start LifeLink:"
echo "   1. Edit .env with your API keys"
echo "   2. Terminal 1: python run_api.py"
echo "   3. Terminal 2: cd frontend && npm run dev"
echo "   4. Open: http://localhost:3000"
echo
echo "📚 See README.md for detailed instructions"