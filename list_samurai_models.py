import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get the SamuraiAPI key
api_key = os.getenv("SAMURAI_API_KEY")

if not api_key:
    print("SAMURAI_API_KEY not found in environment variables")
    exit(1)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

base_url = "https://samuraiapi.in/v1"

print("Querying SamuraiAPI for available models...")
print(f"API Key: {api_key[:10]}...")
print(f"Base URL: {base_url}")
print("-" * 60)

# Try to get the list of models
try:
    response = requests.get(
        f"{base_url}/models",
        headers=headers,
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        print("✅ SUCCESS! Available models:")
        data = response.json()
        
        if 'data' in data:
            models = data['data']
            print(f"\nFound {len(models)} models:")
            print("-" * 40)
            
            for i, model in enumerate(models, 1):
                model_id = model.get('id', 'Unknown')
                model_name = model.get('name', model_id)
                owned_by = model.get('owned_by', 'Unknown')
                
                print(f"{i:2d}. {model_id}")
                if model_name != model_id:
                    print(f"    Name: {model_name}")
                if owned_by != 'Unknown':
                    print(f"    Owner: {owned_by}")
                print()
        else:
            print("Response data:", data)
            
    else:
        print("❌ FAILED to get models list")
        try:
            error_data = response.json()
            print(f"Error: {error_data}")
        except:
            print(f"Raw response: {response.text}")
            
except Exception as e:
    print(f"❌ ERROR: {str(e)}")

print("\n" + "="*60)
print("Alternative: Let's also try some common endpoints...")

# Try alternative endpoints
endpoints_to_try = [
    "/models",
    "/v1/models", 
    "/api/v1/models",
    "/model/list"
]

for endpoint in endpoints_to_try:
    print(f"\nTrying endpoint: {endpoint}")
    try:
        response = requests.get(
            f"https://samuraiapi.in{endpoint}",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print(f"✅ SUCCESS on {endpoint}")
            try:
                data = response.json()
                print(f"Response: {data}")
            except:
                print(f"Response (text): {response.text[:200]}...")
        else:
            print(f"❌ Failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

print("\nModel discovery complete!")