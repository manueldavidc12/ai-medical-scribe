#!/usr/bin/env python3
"""
Production-ready Medical Chatbot Flask App
Vercel-compatible entry point
"""

import os
from web_chatbot import app

# For Vercel deployment
application = app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)