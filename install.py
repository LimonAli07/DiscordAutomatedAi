#!/usr/bin/env python3
"""
Easy installation script for Discord AI Bot.
This script will install all required dependencies and set up the environment.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("   This bot requires Python 3.11 or higher")
        return False

def install_dependencies():
    """Install required dependencies."""
    print("\n📦 Installing Dependencies...")
    print("="*40)
    
    # Check if requirements.txt exists
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt not found!")
        return False
    
    # Install dependencies
    commands = [
        ("pip install --upgrade pip", "Upgrading pip"),
        ("pip install -r requirements.txt", "Installing bot dependencies")
    ]
    
    for command, description in commands:
        if not run_command(command, description):
            return False
    
    return True

def setup_environment():
    """Set up environment files."""
    print("\n⚙️ Setting Up Environment...")
    print("="*35)
    
    # Check if .env exists, if not create from example
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print("📝 Creating .env file from template...")
            try:
                with open(".env.example", 'r') as src, open(".env", 'w') as dst:
                    dst.write(src.read())
                print("✅ .env file created")
                print("⚠️  Please edit .env with your actual Discord bot token and API keys")
            except Exception as e:
                print(f"❌ Failed to create .env file: {e}")
                return False
        else:
            print("❌ .env.example not found!")
            return False
    else:
        print("📁 .env file already exists")
    
    return True

def verify_installation():
    """Verify that everything is installed correctly."""
    print("\n🧪 Verifying Installation...")
    print("="*30)
    
    try:
        # Test imports
        import discord
        print("✅ discord.py imported successfully")
        
        import flask
        print("✅ flask imported successfully")
        
        import openai
        print("✅ openai imported successfully")
        
        import httpx
        print("✅ httpx imported successfully")
        
        import pydantic
        print("✅ pydantic imported successfully")
        
        # Test bot components
        from load_env import load_env_file
        print("✅ Environment loader working")
        
        from simple_fallback import SimpleFallbackAI
        print("✅ Fallback AI working")
        
        print("✅ All components verified successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def main():
    """Main installation process."""
    print("🚀 Discord AI Bot Installation")
    print("="*40)
    print("This script will install all required dependencies for your Discord bot.")
    print()
    
    # Check Python version
    if not check_python_version():
        print("\n💡 Please install Python 3.11 or higher and try again.")
        return False
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Dependency installation failed!")
        return False
    
    # Set up environment
    if not setup_environment():
        print("\n❌ Environment setup failed!")
        return False
    
    # Verify installation
    if not verify_installation():
        print("\n❌ Installation verification failed!")
        return False
    
    # Success message
    print("\n🎉 Installation Complete!")
    print("="*25)
    print("✨ Your Discord bot is ready to set up!")
    print()
    print("📋 Next Steps:")
    print("1. Edit the .env file with your Discord bot token and API keys")
    print("2. Run: python main.py")
    print("3. Invite your bot to a Discord server")
    print("4. Use /askai commands!")
    print()
    print("📖 For detailed setup instructions, see SETUP_GUIDE.md")
    print("🧪 To test your setup, run: python demo_bot.py")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        print("\n❌ Installation failed! Please check the errors above.")
        sys.exit(1)
    else:
        print("\n🎯 Installation successful! Your bot is ready!")
        sys.exit(0)