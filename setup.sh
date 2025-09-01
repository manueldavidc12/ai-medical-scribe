#!/bin/bash
# Medical Chatbot Deployment Setup Script

echo "🏥 Medical Chatbot Deployment Setup"
echo "=================================="

# Check if .env exists
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo "⚠️  Please edit .env file and add your actual API keys!"
else
    echo "✅ .env file already exists"
fi

# Check if git is initialized
if [ ! -d .git ]; then
    echo "📦 Initializing Git repository..."
    git init
    git add .
    git commit -m "Initial commit: Medical Chatbot"
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

echo ""
echo "🎉 Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your API keys"
echo "2. Test locally: python app.py"
echo "3. Push to GitHub: git remote add origin <your-repo-url>"
echo "4. Deploy using Railway/Render/Heroku (see DEPLOYMENT_GUIDE.md)"
echo ""
echo "🚀 Ready for deployment!"