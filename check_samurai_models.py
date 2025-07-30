#!/usr/bin/env python3
"""
Check what models SamuraiAPI actually supports
"""

import asyncio
import sys
import os
import httpx

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import config

async def check_samurai_models():
    """Check what models are available on SamuraiAPI."""
    print("🔍 Checking SamuraiAPI available models...")
    
    if not config.samurai_api_key:
        print("❌ No SamuraiAPI key found")
        return
    
    print(f"✅ API Key found: {config.samurai_api_key[:10]}...")
    
    # Try to get models list
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Try the models endpoint
            models_url = "https://samuraiapi.in/v1/models"
            headers = {
                "Authorization": f"Bearer {config.samurai_api_key}",
                "Content-Type": "application/json"
            }
            
            print(f"📡 Requesting models from: {models_url}")
            response = await client.get(models_url, headers=headers)
            
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ Available models:")
                if "data" in data:
                    for model in data["data"]:
                        print(f"   - {model.get('id', 'Unknown')}")
                else:
                    print(f"   Raw response: {data}")
            else:
                print(f"❌ Error response: {response.text}")
                
        except Exception as e:
            print(f"❌ Error checking models: {e}")
    
    # Test some common models manually
    print("\n🧪 Testing common models manually...")
    
    test_models = [
        "gpt-3.5-turbo",
        "gpt-4",
        "gpt-4o",
        "gpt-4o-mini",
        "claude-3-haiku-20240307",
        "claude-3-sonnet-20240229",
        "llama-3.1-8b-instant",
        "llama-3.1-70b-versatile",
        "gemini-pro",
        "text-davinci-003"
    ]
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for model in test_models:
            try:
                print(f"   Testing model: {model}")
                
                test_data = {
                    "model": model,
                    "messages": [
                        {"role": "user", "content": "Hello"}
                    ],
                    "max_tokens": 10
                }
                
                headers = {
                    "Authorization": f"Bearer {config.samurai_api_key}",
                    "Content-Type": "application/json"
                }
                
                response = await client.post(
                    "https://samuraiapi.in/v1/chat/completions",
                    headers=headers,
                    json=test_data,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    print(f"   ✅ {model} - WORKS")
                elif response.status_code == 429:
                    print(f"   ⚠️  {model} - Rate limited (but model exists)")
                elif response.status_code == 503:
                    print(f"   ⚠️  {model} - Service unavailable (but model exists)")
                else:
                    print(f"   ❌ {model} - Error {response.status_code}: {response.text[:100]}")
                    
            except asyncio.TimeoutError:
                print(f"   ⏰ {model} - Timeout")
            except Exception as e:
                print(f"   ❌ {model} - Exception: {e}")
            
            # Small delay to avoid rate limits
            await asyncio.sleep(0.5)

async def main():
    """Main function."""
    print("🚀 SamuraiAPI Model Checker")
    print("=" * 50)
    
    await check_samurai_models()
    
    print("\n" + "=" * 50)
    print("✅ Model check complete!")

if __name__ == "__main__":
    asyncio.run(main())