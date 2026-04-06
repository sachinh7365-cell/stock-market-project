#!/bin/bash
# Local development setup script

echo "Setting up Stock Market Prediction application for local development..."

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  Please update .env with your MongoDB connection string and SECRET_KEY"
    echo "   Edit .env and set:"
    echo "   - MONGO_URI=your_mongodb_uri"
    echo "   - SECRET_KEY=your_secret_key"
fi

echo ""
echo "✅ Setup complete! To start the development server:"
echo "   1. Update .env with your MongoDB URI and SECRET_KEY"
echo "   2. Run: python app.py"
echo ""
