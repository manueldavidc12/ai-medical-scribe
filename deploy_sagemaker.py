#!/usr/bin/env python3
"""
Deploy II-Medical-8B model to Amazon SageMaker
Based on the provided template
"""

import json
import sagemaker
import boto3
from sagemaker.huggingface import HuggingFaceModel, get_huggingface_llm_image_uri

def deploy_medical_model():
    """Deploy II-Medical-8B to SageMaker"""
    
    print("🚀 Starting SageMaker deployment for II-Medical-8B...")
    
    # Get execution role
    try:
        role = sagemaker.get_execution_role()
        print(f"✅ Using SageMaker execution role: {role}")
    except ValueError:
        print("⚠️  Getting IAM role (not in SageMaker environment)")
        iam = boto3.client('iam')
        role = iam.get_role(RoleName='sagemaker_execution_role')['Role']['Arn']
        print(f"✅ Using IAM role: {role}")

    # Hub Model configuration
    hub = {
        'HF_MODEL_ID': 'Intelligent-Internet/II-Medical-8B',  # Your model
        'SM_NUM_GPUS': json.dumps(1),
        'HF_TASK': 'text-generation'
    }

    print(f"📋 Model configuration:")
    print(f"   - Model: {hub['HF_MODEL_ID']}")
    print(f"   - GPUs: {hub['SM_NUM_GPUS']}")

    # Create Hugging Face Model Class
    try:
        huggingface_model = HuggingFaceModel(
            image_uri=get_huggingface_llm_image_uri("huggingface", version="3.2.3"),
            env=hub,
            role=role, 
        )
        print("✅ HuggingFace model class created")
    except Exception as e:
        print(f"❌ Failed to create model class: {e}")
        return None

    # Deploy model to SageMaker Inference
    print("🔄 Deploying to SageMaker (this may take 10-15 minutes)...")
    print("   Instance: ml.g5.2xlarge")
    print("   Timeout: 300 seconds")
    
    try:
        predictor = huggingface_model.deploy(
            initial_instance_count=1,
            instance_type="ml.g5.2xlarge",
            container_startup_health_check_timeout=300,
        )
        
        endpoint_name = predictor.endpoint_name
        print(f"🎉 Deployment successful!")
        print(f"📍 Endpoint name: {endpoint_name}")
        
        # Test the deployment
        print("\n🧪 Testing deployment...")
        test_response = predictor.predict({
            "inputs": "Hello, I am a medical AI assistant. How can I help you today?",
            "parameters": {
                "max_new_tokens": 50,
                "temperature": 0.1
            }
        })
        
        print("✅ Test successful!")
        print(f"Test response: {test_response}")
        
        print("\n📝 Next steps:")
        print(f"1. Update simple_medical_chat.py with endpoint name:")
        print(f"   endpoint_name = '{endpoint_name}'")
        print(f"2. Run: python3 simple_medical_chat.py")
        print(f"3. Open: http://localhost:5000")
        
        return predictor
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Check AWS credentials: aws configure list")
        print("2. Verify SageMaker permissions")
        print("3. Ensure ml.g5.2xlarge is available in your region")
        return None

def cleanup_endpoint(endpoint_name):
    """Delete SageMaker endpoint to avoid costs"""
    try:
        sagemaker_client = boto3.client('sagemaker')
        sagemaker_client.delete_endpoint(EndpointName=endpoint_name)
        print(f"🗑️  Endpoint {endpoint_name} deleted to avoid costs")
    except Exception as e:
        print(f"❌ Failed to delete endpoint: {e}")

if __name__ == '__main__':
    print("🩺 II-Medical-8B SageMaker Deployment")
    print("=" * 50)
    
    # Deploy the model
    predictor = deploy_medical_model()
    
    if predictor:
        endpoint_name = predictor.endpoint_name
        print(f"\n💰 Cost warning: ml.g5.2xlarge costs ~$1.20/hour")
        print(f"Don't forget to delete the endpoint when done:")
        print(f"python3 -c \"from deploy_sagemaker import cleanup_endpoint; cleanup_endpoint('{endpoint_name}')\"")
    
    print("\nDeployment script completed!")