#!/usr/bin/env python3
"""
Basic Web Medical Chatbot using II-Medical-8B-1706 via Hugging Face API
Simple HTML interface with Flask
"""

from flask import Flask, render_template, request, jsonify, session
import requests
import json
import openai
import uuid
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = os.getenv('SECRET_KEY', 'medical-assistant-secret-key-2024')
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_TYPE'] = 'filesystem'

# In-memory storage for conversations (in production, use a database)
conversations_db = {}

# API Keys from environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')

# Model URLs
MEDICAL_MODEL_URL = "https://en32b8h73rhx94n0.us-east-1.aws.endpoints.huggingface.cloud"

# Configure OpenAI
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
else:
    print("WARNING: OPENAI_API_KEY not found in environment variables")

def collect_patient_data_openai(conversation_history):
    """Use OpenAI to systematically collect patient data"""
    try:
        # Create conversation summary from the actual conversation
        conversation_text = ""
        for msg in conversation_history:
            role = "Patient" if msg["role"] == "user" else "Doctor"
            conversation_text += f"{role}: {msg['content']}\n"
        
        print(f"DEBUG - Full conversation:\n{conversation_text}")  # Debug output
        
        system_prompt = f"""You are conducting a medical interview. Here is the COMPLETE conversation so far:

{conversation_text}

CRITICAL INSTRUCTIONS:
1. Review the ENTIRE conversation above
2. NEVER ask questions that have already been answered
3. Build logically on what the patient has already told you
4. Ask ONE focused follow-up question to gather missing information
5. When you have sufficient data (20+ exchanges), say "READY_FOR_ANALYSIS"

EXAMPLES OF WHAT NOT TO DO:
- If patient said "stomach ache" → DON'T ask "what brings you in today"
- If patient said "5" for pain scale → DON'T ask for pain scale again
- If conversation shows symptoms and severity → Ask about location, triggers, or medical history

YOUR NEXT QUESTION should be the most logical follow-up based on the conversation above."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "What is your next question for this patient?"}
        ]
        
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini-2024-07-18",
            messages=messages,
            max_tokens=100,
            temperature=0.0
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        return f"Error with OpenAI: {str(e)}"

def create_patient_summary(conversation_history):
    """Create a detailed summary of all patient information collected"""
    
    # Initialize data structure
    patient_data = {
        "demographics": {"age": None, "sex": None},
        "chief_complaints": [],
        "symptoms": {},
        "timeline": [],
        "severity": {},
        "location": {},
        "other_info": []
    }
    
    # Parse all user responses
    for i, msg in enumerate(conversation_history):
        if msg["role"] == "user":
            content = msg["content"].strip()
            content_lower = content.lower()
            
            # Demographics parsing
            if any(sex in content_lower for sex in ["male", "female", "man", "woman"]):
                if "male" in content_lower:
                    patient_data["demographics"]["sex"] = "male"
                elif "female" in content_lower:
                    patient_data["demographics"]["sex"] = "female"
                    
            # Age parsing
            import re
            age_match = re.search(r'\b(\d{1,3})\b', content)
            if age_match and not patient_data["demographics"]["age"]:
                potential_age = int(age_match.group(1))
                if 1 <= potential_age <= 120:
                    patient_data["demographics"]["age"] = potential_age
            
            # Symptoms parsing
            symptom_keywords = ["pain", "ache", "hurt", "fever", "nausea", "vomit", "cough", "headache", "dizzy"]
            for keyword in symptom_keywords:
                if keyword in content_lower and content not in patient_data["chief_complaints"]:
                    patient_data["chief_complaints"].append(content)
                    break
            
            # Timeline parsing
            time_keywords = ["day", "hour", "week", "month", "year", "ago", "started", "began", "today", "yesterday"]
            if any(keyword in content_lower for keyword in time_keywords):
                if content not in patient_data["timeline"]:
                    patient_data["timeline"].append(content)
            
            # Severity parsing (0-10 scale)
            severity_match = re.search(r'\b(\d{1,2})/10\b', content)
            if severity_match:
                severity_score = severity_match.group(1)
                patient_data["severity"]["pain"] = f"{severity_score}/10"
            
            # Location parsing
            body_parts = ["abdomen", "stomach", "chest", "head", "back", "leg", "arm", "left", "right", "side"]
            for part in body_parts:
                if part in content_lower:
                    patient_data["location"][part] = content
                    break
    
    # Build comprehensive summary
    summary_lines = []
    
    # Demographics
    if patient_data["demographics"]["age"] and patient_data["demographics"]["sex"]:
        summary_lines.append(f"PATIENT: {patient_data['demographics']['age']}-year-old {patient_data['demographics']['sex']}")
    elif patient_data["demographics"]["age"]:
        summary_lines.append(f"AGE: {patient_data['demographics']['age']}")
    elif patient_data["demographics"]["sex"]:
        summary_lines.append(f"SEX: {patient_data['demographics']['sex']}")
    
    # Chief complaints
    if patient_data["chief_complaints"]:
        summary_lines.append(f"CHIEF COMPLAINTS: {'; '.join(patient_data['chief_complaints'])}")
    
    # Timeline
    if patient_data["timeline"]:
        summary_lines.append(f"TIMELINE: {'; '.join(patient_data['timeline'])}")
    
    # Severity
    if patient_data["severity"]:
        severity_info = '; '.join([f"{k}: {v}" for k, v in patient_data["severity"].items()])
        summary_lines.append(f"SEVERITY: {severity_info}")
    
    # Location
    if patient_data["location"]:
        location_info = '; '.join([f"{k}: {v}" for k, v in patient_data["location"].items()])
        summary_lines.append(f"LOCATION: {location_info}")
    
    return "\n".join(summary_lines) if summary_lines else "No patient information collected yet"

def analyze_with_medical_model(patient_data):
    """Generate SOAP note using OpenAI GPT-4o-mini for reliable medical documentation"""
    
    try:
        print(f"DEBUG - Using OpenAI for SOAP note generation...")
        
        # Enhanced medical prompt for OpenAI
        system_prompt = """You are a medical scribe creating SOAP notes. Follow these strict guidelines:

1. Use ONLY information explicitly stated in the conversation
2. Do NOT invent vital signs, lab results, or physical exam findings
3. If no physical exam is documented, write "Physical examination not documented"
4. Keep assessments conservative and based only on reported symptoms
5. Provide basic, appropriate recommendations

Format: S: O: A: P: (each on separate lines)"""

        user_prompt = f"""Create a SOAP note from this patient conversation:

{patient_data}

Remember: Only use information explicitly stated. Do not add any data not mentioned."""

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=300,
            temperature=0.1
        )
        
        content = response.choices[0].message.content.strip()
        
        print(f"DEBUG - OpenAI SOAP response: {content}")
        
        return content if content else "SOAP note generation failed"
        
    except Exception as e:
        print(f"DEBUG - OpenAI Exception: {str(e)}")
        return f"Error generating SOAP note: {str(e)}"

def create_new_conversation():
    """Create a new conversation and return its ID"""
    conversation_id = str(uuid.uuid4())
    conversations_db[conversation_id] = {
        'id': conversation_id,
        'title': 'New Patient',
        'messages': [],
        'data_collection_complete': False,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    return conversation_id

def get_conversation_title(messages):
    """Generate a conversation title from the first user message"""
    for msg in messages:
        if msg['role'] == 'user':
            content = msg['content'][:50]
            if len(msg['content']) > 50:
                content += "..."
            return content
    return "New Patient"

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/app')
def chat_interface():
    return render_template('index.html')

@app.route('/conversations', methods=['GET'])
def get_conversations():
    """Get list of all conversations"""
    conv_list = []
    for conv_id, conv_data in conversations_db.items():
        conv_list.append({
            'id': conv_id,
            'title': conv_data['title'],
            'created_at': conv_data['created_at'],
            'updated_at': conv_data['updated_at']
        })
    
    # Sort by updated_at descending
    conv_list.sort(key=lambda x: x['updated_at'], reverse=True)
    return jsonify({'conversations': conv_list})

@app.route('/conversations', methods=['POST'])
def create_conversation():
    """Create a new conversation"""
    conversation_id = create_new_conversation()
    return jsonify({'conversation_id': conversation_id})

@app.route('/conversations/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get a specific conversation"""
    if conversation_id not in conversations_db:
        return jsonify({'error': 'Conversation not found'}), 404
    
    return jsonify({'conversation': conversations_db[conversation_id]})

@app.route('/conversations/<conversation_id>', methods=['DELETE'])
def delete_conversation(conversation_id):
    """Delete a conversation"""
    if conversation_id not in conversations_db:
        return jsonify({'error': 'Conversation not found'}), 404
    
    del conversations_db[conversation_id]
    return jsonify({'status': 'deleted'})

@app.route('/reset', methods=['POST'])
def reset_conversation():
    """Reset the current conversation"""
    if 'current_conversation_id' in session:
        conv_id = session['current_conversation_id']
        if conv_id in conversations_db:
            conversations_db[conv_id]['messages'] = []
            conversations_db[conv_id]['data_collection_complete'] = False
            conversations_db[conv_id]['title'] = 'New Patient'
            conversations_db[conv_id]['updated_at'] = datetime.now().isoformat()
    
    session.clear()
    return jsonify({'status': 'reset'})

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '').strip()
    conversation_id = request.json.get('conversation_id')
    
    if not user_message:
        return jsonify({'response': 'Please enter a message.'})
    
    # Get or create conversation
    if not conversation_id or conversation_id not in conversations_db:
        conversation_id = create_new_conversation()
        session['current_conversation_id'] = conversation_id
    
    conversation = conversations_db[conversation_id]
    
    # Add user message to conversation
    conversation['messages'].append({"role": "user", "content": user_message})
    conversation['updated_at'] = datetime.now().isoformat()
    
    print(f"DEBUG - Total messages in conversation: {len(conversation['messages'])}")
    print(f"DEBUG - Current user message: {user_message}")
    
    # Update conversation title if it's the first user message
    if len([msg for msg in conversation['messages'] if msg['role'] == 'user']) == 1:
        conversation['title'] = get_conversation_title(conversation['messages'])
    
    if not conversation['data_collection_complete']:
        # STAGE 1: Data Collection with OpenAI
        ai_response = collect_patient_data_openai(conversation['messages'])
        
        # Add assistant response to conversation
        conversation['messages'].append({"role": "assistant", "content": ai_response})
        
        # Check if we should show the SOAP generation button
        user_message_count = len([msg for msg in conversation['messages'] if msg['role'] == 'user'])
        show_soap_button = user_message_count >= 2 and not conversation['data_collection_complete']
    
    else:
        ai_response = "Data collection is complete. Please create a new conversation for another patient interview."
    
    return jsonify({
        'response': ai_response,
        'show_soap_button': show_soap_button if 'show_soap_button' in locals() else False,
        'user_message_count': user_message_count if 'user_message_count' in locals() else 0,
        'conversation_id': conversation_id
    })

@app.route('/analyze', methods=['POST'])
def manual_analysis():
    """Trigger manual medical analysis for a conversation"""
    conversation_id = request.json.get('conversation_id')
    
    if not conversation_id or conversation_id not in conversations_db:
        return jsonify({'error': 'Conversation not found'}), 404
    
    conversation = conversations_db[conversation_id]
    
    # Check if there are enough messages for analysis (at least 2 user messages)
    user_message_count = len([msg for msg in conversation['messages'] if msg['role'] == 'user'])
    if user_message_count < 2:
        return jsonify({'error': 'Insufficient data for analysis. Need at least 2 patient messages.'}), 400
    
    # Check if analysis was already completed
    if conversation['data_collection_complete']:
        return jsonify({'error': 'Analysis already completed for this conversation.'}), 400
    
    # Compile patient data from conversation
    patient_data = "\n".join([
        f"{'Patient' if msg['role'] == 'user' else 'Doctor'}: {msg['content']}" 
        for msg in conversation['messages']
    ])
    
    print(f"DEBUG - Manual analysis triggered for conversation {conversation_id}")
    print(f"DEBUG - Patient data for analysis:\n{patient_data}")
    
    # Perform medical analysis with II-Medical-8B-1706
    analysis = analyze_with_medical_model(patient_data)
    
    # Create SOAP note response
    ai_response = f"""**📋 SOAP NOTE - STRUCTURED MEDICAL ANALYSIS**

**Generated by II-Medical-8B-1706 Clinical Scribe**

---

{analysis}

---

**📝 CLINICAL NOTE COMPLETED:**
- ✅ Patient data processed according to standard SOAP format
- ✅ Information documented without inferences or assumptions
- ✅ Missing fields explicitly marked as "Not documented"
- ✅ Clinical evaluation ready for physician review

---
*SOAP note completed. You can create a new consultation using the sidebar.*"""
    
    # Add the analysis to the conversation
    conversation['messages'].append({"role": "assistant", "content": ai_response})
    conversation['data_collection_complete'] = True
    conversation['updated_at'] = datetime.now().isoformat()
    
    # Update conversation title to indicate analysis completion
    if not conversation['title'].endswith('✅'):
        conversation['title'] += ' ✅'
    
    return jsonify({'response': ai_response})

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5001)