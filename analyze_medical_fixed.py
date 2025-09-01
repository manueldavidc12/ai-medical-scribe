import requests
import os

def analyze_with_medical_model_fixed(patient_data, api_key):
    """Fixed version using OpenAI-compatible endpoint"""
    
    medical_prompt = f"""You are a medical doctor. Create a SOAP note from this patient conversation.

{patient_data}

Create a SOAP note:
S:"""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Use OpenAI-compatible endpoint format
    payload = {
        "prompt": medical_prompt,
        "max_tokens": 400,
        "temperature": 0.2,
    }
    
    try:
        print(f"DEBUG - Using OpenAI-compatible endpoint...")
        url = "https://en32b8h73rhx94n0.us-east-1.aws.endpoints.huggingface.cloud/v1/completions"
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            print(f"DEBUG - Full API response: {result}")
            
            content = result.get("choices", [{}])[0].get("text", "").strip()
            
            print(f"DEBUG - Response length: {len(content)}")
            print(f"DEBUG - Content: {content}")
            
            return content if content else "SOAP note generation in progress..."
        else:
            print(f"DEBUG - API Error {response.status_code}: {response.text}")
            return f"Unable to generate SOAP note (Status: {response.status_code})"
            
    except Exception as e:
        print(f"DEBUG - Exception: {str(e)}")
        return f"Error: {str(e)}"

# Test the function
if __name__ == "__main__":
    test_data = """Patient: nails weak, women, 25 years old
Doctor: Have you noticed any other symptoms accompanying your weak nails?
Patient: 2 weeks nails breaking, started after nail treatment"""
    
    # Use environment variable for API key
    api_key = os.getenv('HUGGINGFACE_API_KEY', 'your-huggingface-api-key-here')
    result = analyze_with_medical_model_fixed(test_data, api_key)
    print("RESULT:", result)