#!/usr/bin/env python3
"""
Environment variable loader for Discord bot.
Loads variables from .env file if it exists.
"""

import os
from pathlib import Path

def load_env_file(env_file_path=".env"):
    """
    Load environment variables from a .env file.
    
    Args:
        env_file_path (str): Path to the .env file
    """
    env_path = Path(env_file_path)
    
    if not env_path.exists():
        print(f"⚠️ No {env_file_path} file found. Using system environment variables.")
        return False
    
    print(f"📁 Loading environment variables from {env_file_path}")
    
    try:
        with open(env_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        loaded_vars = []
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Parse KEY=VALUE format
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                # Only set if not already in environment (system env takes precedence)
                if key not in os.environ and value and value != 'your_' + key.lower() + '_here':
                    os.environ[key] = value
                    loaded_vars.append(key)
                elif key in os.environ:
                    print(f"  ⚠️ {key} already set in system environment, skipping")
                elif not value or value.startswith('your_'):
                    print(f"  ⚠️ {key} has placeholder value, skipping")
            else:
                print(f"  ⚠️ Line {line_num}: Invalid format (expected KEY=VALUE): {line}")
        
        if loaded_vars:
            print(f"✅ Loaded {len(loaded_vars)} environment variables: {', '.join(loaded_vars)}")
        else:
            print("⚠️ No new environment variables loaded (all were already set or had placeholder values)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error loading {env_file_path}: {e}")
        return False

def check_required_vars():
    """Check if required environment variables are set."""
    required_vars = {
        'DISCORD_BOT_TOKEN': 'Discord bot token',
        'DISCORD_OWNER_ID': 'Discord owner user ID'
    }
    
    api_keys = {
        'GPT4ALL_API_KEY': 'GPT4All API key',
        'OPENAI_API_KEY': 'OpenAI/OpenRouter API key', 
        'GOOGLE_AI_KEY': 'Google AI Studio API key',
        'CEREBRAS_API_KEY': 'Cerebras API key'
    }
    
    missing_required = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_required.append(f"{var} ({description})")
    
    available_apis = []
    for var, description in api_keys.items():
        if os.getenv(var):
            available_apis.append(description)
    
    print("\n📊 Environment Variable Status:")
    print("="*40)
    
    # Check required variables
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            masked_value = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"❌ {var}: Not set")
    
    # Check API keys
    print(f"\n🔑 API Keys Available: {len(available_apis)}")
    for description in available_apis:
        print(f"✅ {description}")
    
    if not available_apis:
        print("❌ No API keys found - bot will use fallback AI only")
    
    if missing_required:
        print(f"\n⚠️ Missing required variables:")
        for var in missing_required:
            print(f"  - {var}")
        return False
    
    print(f"\n🎉 All required variables are set!")
    return True

def create_env_file():
    """Create a .env file from the example if it doesn't exist."""
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print("📝 Creating .env file from .env.example...")
            try:
                with open(".env.example", 'r') as src, open(".env", 'w') as dst:
                    dst.write(src.read())
                print("✅ Created .env file. Please edit it with your actual values.")
                return True
            except Exception as e:
                print(f"❌ Error creating .env file: {e}")
                return False
        else:
            print("❌ No .env.example file found to copy from")
            return False
    else:
        print("📁 .env file already exists")
        return True

if __name__ == "__main__":
    print("🔧 Discord Bot Environment Setup")
    print("="*40)
    
    # Create .env file if it doesn't exist
    create_env_file()
    
    # Load environment variables
    load_env_file()
    
    # Check status
    check_required_vars()
    
    print("\n💡 Next steps:")
    print("1. Edit the .env file with your actual API keys")
    print("2. Run: python main.py")
    print("3. Invite your bot to a Discord server")
    print("4. Use /askai commands!")