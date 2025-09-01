#!/usr/bin/env python3
"""
Production-ready Medical Chatbot Flask App
Entry point for deployment
"""

import os
from web_chatbot import app

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)