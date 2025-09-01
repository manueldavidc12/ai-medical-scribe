#!/usr/bin/env python3
"""
Basic Medical Chatbot using II-Medical-8B-1706 via Hugging Face API
Simple command-line interface
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Your Hugging Face API Key from environment
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
MODEL_URL = "https://api-inference.huggingface.co/models/Intelligent-Internet/II-Medical-8B-1706"

def query_medical_model(prompt):
    """Send a prompt to II-Medical-8B-1706 and get response"""
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 300,
            "temperature": 0.1,
            "do_sample": True,
            "return_full_text": False
        }
    }
    
    try:
        response = requests.post(MODEL_URL, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("generated_text", "").strip()
            elif isinstance(result, dict):
                return result.get("generated_text", "").strip()
        else:
            return f"API Error: {response.status_code} - {response.text}"
            
    except Exception as e:
        return f"Error: {str(e)}"

def main():
    print("🩺 Medical AI Chatbot")
    print("Powered by II-Medical-8B-1706")
    print("-" * 50)
    print("Type your medical questions or symptoms.")
    print("Type 'quit' to exit.")
    print("-" * 50)
    
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()
        
        # Check for exit command
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("\nGoodbye! Remember to consult healthcare professionals for medical advice.")
            break
        
        if not user_input:
            continue
            
        # Create medical prompt
        medical_prompt = f"""You are a medical AI assistant. A patient asks: "{user_input}"

Provide a helpful medical response including possible conditions and recommendations. Be concise but thorough."""
        
        print("\n🤖 Medical AI: ", end="", flush=True)
        
        # Get AI response
        response = query_medical_model(medical_prompt)
        print(response)
        
        # Medical disclaimer
        if len(response) > 50:  # Only show disclaimer for substantial responses
            print("\n⚠️  Disclaimer: This is AI-generated information. Consult healthcare professionals for proper diagnosis and treatment.")

if __name__ == "__main__":
    main()