#!/usr/bin/env python
"""
Setup script for NeuroData backend development environment.
"""
import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return None

def main():
    """Main setup function."""
    print("🚀 Setting up NeuroData Backend Development Environment")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not Path("manage.py").exists():
        print("❌ Please run this script from the backend directory")
        sys.exit(1)
    
    # Create virtual environment
    if not Path("venv").exists():
        run_command("python -m venv venv", "Creating virtual environment")
    else:
        print("✅ Virtual environment already exists")
    
    # Activate virtual environment and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/Mac
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    # Install dependencies
    run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip")
    run_command(f"{pip_cmd} install -r requirements-dev.txt", "Installing dependencies")
    
    # Create .env file if it doesn't exist
    if not Path(".env").exists():
        print("🔄 Creating .env file from template...")
        with open(".env.example", "r") as source:
            content = source.read()
        with open(".env", "w") as target:
            target.write(content)
        print("✅ .env file created (please update with your settings)")
    else:
        print("✅ .env file already exists")
    
    # Create logs directory
    logs_dir = Path("logs")
    if not logs_dir.exists():
        logs_dir.mkdir()
        print("✅ Logs directory created")
    
    # Create media directories
    media_dirs = ["media/datasets", "media/models", "media/temp"]
    for dir_path in media_dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    print("✅ Media directories created")
    
    print("\n" + "=" * 60)
    print("🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Update the .env file with your database and API credentials")
    print("2. Start PostgreSQL and Redis services")
    print("3. Run: python manage.py migrate")
    print("4. Run: python manage.py createsuperuser")
    print("5. Run: python manage.py runserver")
    print("\nFor development with auto-reload:")
    if os.name == 'nt':
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    print("   python manage.py runserver")

if __name__ == "__main__":
    main()
