#!/usr/bin/env python3
"""
Simple Medical Chatbot Backend for II-Medical-8B on SageMaker
Clean, minimal implementation
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import uuid
from datetime import datetime

# Import AWS dependencies only when needed
sagemaker_predictor = None

try:
    import boto3
    import sagemaker
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    print("⚠️  AWS dependencies not installed - SageMaker features disabled")

app = Flask(__name__)
CORS(app)

# Global variables
conversations = {}
sagemaker_predictor = None

def initialize_sagemaker():
    """Initialize SageMaker predictor for II-Medical-8B model"""
    global sagemaker_predictor
    
    if not AWS_AVAILABLE:
        print("❌ AWS dependencies not available")
        return False
    
    try:
        # Get SageMaker execution role
        try:
            role = sagemaker.get_execution_role()
        except ValueError:
            iam = boto3.client('iam')
            role = iam.get_role(RoleName='sagemaker_execution_role')['Role']['Arn']
        
        # You'll need to replace this with your actual endpoint name after deployment
        endpoint_name = "huggingface-pytorch-tgi-inference-2024-08-31-14-30-00-000"  # Update this!
        
        # Create predictor
        from sagemaker.huggingface import HuggingFacePredictor
        sagemaker_predictor = HuggingFacePredictor(
            endpoint_name=endpoint_name
        )
        
        print(f"✅ SageMaker predictor initialized with endpoint: {endpoint_name}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to initialize SageMaker: {str(e)}")
        print("💡 Make sure you've deployed the model and updated the endpoint_name")
        return False

def mock_medical_ai(messages):
    """Mock medical AI for testing without SageMaker"""
    user_count = len([msg for msg in messages if msg['role'] == 'user'])
    
    if user_count == 1:
        return "Thank you for sharing your symptoms. Can you tell me when these symptoms first started and how severe they are on a scale of 1-10?"
    elif user_count == 2:
        return "I see. Have you tried any treatments or medications for this condition, and do you have any relevant medical history I should know about?"
    else:
        # Generate mock SOAP note
        return """S: Patient reports symptoms as described in our conversation. Duration and severity noted as per patient's account.

O: Physical examination not performed (telemedicine consultation). Vital signs not documented.

A: Based on the presented symptoms and patient history, this appears to be a condition requiring further evaluation. Differential diagnosis should be considered.

P: Recommend consultation with primary care physician for physical examination. Consider relevant diagnostic tests based on symptoms. Patient education provided regarding symptom monitoring."""

def chat_with_medical_ai(messages):
    """Send conversation to II-Medical-8B model via SageMaker"""
    
    # Use mock AI if SageMaker is not available
    if not sagemaker_predictor:
        return mock_medical_ai(messages)
    
    try:
        # Count user messages to determine if we should ask questions or give SOAP note
        user_count = len([msg for msg in messages if msg['role'] == 'user'])
        
        # Format conversation
        conversation = "\n".join([
            f"{'Patient' if msg['role'] == 'user' else 'Doctor'}: {msg['content']}"
            for msg in messages
        ])
        
        if user_count <= 2:
            # Ask medical questions
            prompt = f"""<|im_start|>system
You are a medical doctor interviewing a patient. Ask ONE focused medical question to understand their condition better. Be professional and direct.<|im_end|>
<|im_start|>user
Current conversation:
{conversation}

What medical question should you ask next?<|im_end|>
<|im_start|>assistant"""
        else:
            # Generate SOAP note
            prompt = f"""<|im_start|>system  
You are a medical doctor. Create a SOAP note based on the patient information. Use this format:

S: [Patient's subjective complaints]
O: [Objective findings - write "Not documented" if missing]
A: [Your medical assessment]  
P: [Treatment plan and recommendations]<|im_end|>
<|im_start|>user
Patient conversation:
{conversation}

Create a SOAP note:<|im_end|>
<|im_start|>assistant"""

        # Send to SageMaker
        response = sagemaker_predictor.predict({
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 200,
                "temperature": 0.1,
                "do_sample": True
            }
        })
        
        # Extract response
        if isinstance(response, list) and len(response) > 0:
            content = response[0].get('generated_text', '').strip()
        else:
            content = response.get('generated_text', '').strip()
        
        # Clean response
        content = content.replace('<|im_end|>', '').strip()
        
        return content if content else "Could you please provide more details about your symptoms?"
        
    except Exception as e:
        print(f"Error with medical AI: {str(e)}")
        return f"I'm having difficulty processing your request. Please try again."

@app.route('/')
def home():
    """Simple chat interface"""
    return render_template_string('''
<!DOCTYPE html>
<html>
<head>
    <title>Medical AI Chatbot</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .chat-container { border: 1px solid #ddd; height: 400px; overflow-y: auto; padding: 10px; margin-bottom: 10px; }
        .message { margin: 10px 0; padding: 10px; border-radius: 5px; }
        .user { background-color: #e3f2fd; text-align: right; }
        .assistant { background-color: #f5f5f5; }
        .input-container { display: flex; }
        .input-container input { flex: 1; padding: 10px; }
        .input-container button { padding: 10px 20px; }
        .new-conversation { margin-bottom: 10px; }
    </style>
</head>
<body>
    <h1>🩺 Medical AI Assistant</h1>
    <p>Powered by II-Medical-8B on Amazon SageMaker</p>
    
    <button class="new-conversation" onclick="newConversation()">New Consultation</button>
    
    <div class="chat-container" id="chatContainer"></div>
    
    <div class="input-container">
        <input type="text" id="messageInput" placeholder="Describe your symptoms..." onkeypress="handleKeyPress(event)">
        <button onclick="sendMessage()">Send</button>
    </div>

    <script>
        let currentConversationId = null;
        
        function newConversation() {
            currentConversationId = null;
            document.getElementById('chatContainer').innerHTML = '';
        }
        
        function handleKeyPress(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        }
        
        async function sendMessage() {
            const input = document.getElementById('messageInput');
            const message = input.value.trim();
            if (!message) return;
            
            // Add user message to chat
            addMessage(message, 'user');
            input.value = '';
            
            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: message,
                        conversation_id: currentConversationId
                    })
                });
                
                const data = await response.json();
                currentConversationId = data.conversation_id;
                
                // Add AI response to chat
                addMessage(data.response, 'assistant');
                
            } catch (error) {
                addMessage('Error: Could not connect to the medical AI.', 'assistant');
            }
        }
        
        function addMessage(content, role) {
            const chatContainer = document.getElementById('chatContainer');
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;
            messageDiv.innerHTML = `<strong>${role === 'user' ? 'You' : 'Doctor'}:</strong> ${content}`;
            chatContainer.appendChild(messageDiv);
            chatContainer.scrollTop = chatContainer.scrollHeight;
        }
    </script>
</body>
</html>
    ''')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    data = request.json
    message = data.get('message', '').strip()
    conversation_id = data.get('conversation_id')
    
    if not message:
        return jsonify({'error': 'Message is required'}), 400
    
    # Create new conversation if needed
    if not conversation_id or conversation_id not in conversations:
        conversation_id = str(uuid.uuid4())
        conversations[conversation_id] = {
            'id': conversation_id,
            'messages': [],
            'created_at': datetime.now().isoformat()
        }
    
    conversation = conversations[conversation_id]
    
    # Add user message
    conversation['messages'].append({'role': 'user', 'content': message})
    
    # Get AI response
    ai_response = chat_with_medical_ai(conversation['messages'])
    
    # Add AI response  
    conversation['messages'].append({'role': 'assistant', 'content': ai_response})
    
    return jsonify({
        'response': ai_response,
        'conversation_id': conversation_id
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    status = "SageMaker Ready" if sagemaker_predictor else "SageMaker Not Connected"
    return jsonify({'status': status})

if __name__ == '__main__':
    print("🚀 Starting Medical AI Chatbot...")
    print("📋 Features:")
    print("   - II-Medical-8B model via Amazon SageMaker")
    print("   - Doctor asks 2 questions, then provides SOAP note")
    print("   - Simple web interface at http://localhost:5000")
    
    # Initialize SageMaker (optional - can work without it for testing)
    sagemaker_ready = initialize_sagemaker()
    
    if not sagemaker_ready:
        print("⚠️  SageMaker not connected - update endpoint_name in code after deployment")
    
    print("\n🌐 Starting server...")
    app.run(debug=True, host='127.0.0.1', port=5002)