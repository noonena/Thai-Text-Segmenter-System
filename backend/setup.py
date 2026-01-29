#!/usr/bin/env python3
"""
Cross-platform setup script for Thai Text Segmenter Backend
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

# ANSI color codes
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    RED = '\033[0;31m'
    NC = '\033[0m'  # No Color
    
    @staticmethod
    def disable():
        """Disable colors on Windows if not supported"""
        if platform.system() == 'Windows':
            Colors.GREEN = ''
            Colors.YELLOW = ''
            Colors.BLUE = ''
            Colors.RED = ''
            Colors.NC = ''

def print_colored(message, color=Colors.NC):
    """Print colored message"""
    print(f"{color}{message}{Colors.NC}")

def run_command(command, description, check=True):
    """Run a command and handle errors"""
    print_colored(f"\n{description}...", Colors.YELLOW)
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_colored(f"✓ {description} completed", Colors.GREEN)
            return True
        else:
            print_colored(f"✗ {description} failed", Colors.RED)
            if result.stderr:
                print(result.stderr)
            return False
    except subprocess.CalledProcessError as e:
        print_colored(f"✗ Error: {e}", Colors.RED)
        return False

def main():
    """Main setup function"""
    
    # Detect Windows and disable colors if needed
    if platform.system() == 'Windows':
        Colors.disable()
    
    print_colored("=" * 50, Colors.BLUE)
    print_colored("Thai Text Segmenter - Backend Setup", Colors.BLUE)
    print_colored("=" * 50, Colors.BLUE)
    
    # Detect OS
    os_name = platform.system()
    os_version = platform.version()
    print_colored(f"\nDetected OS: {os_name} ({os_version})", Colors.YELLOW)
    
    # Check Python version
    python_version = sys.version.split()[0]
    print_colored(f"Python Version: {python_version}", Colors.GREEN)
    
    if sys.version_info < (3, 8):
        print_colored("Error: Python 3.8 or higher is required!", Colors.RED)
        sys.exit(1)
    
    # Get backend directory (where this script is located)
    backend_dir = Path(__file__).parent.absolute()
    
    print_colored(f"\nWorking directory: {backend_dir}", Colors.YELLOW)
    
    # Verify we have the expected structure
    scripts_dir = backend_dir / "scripts"
    if not scripts_dir.exists():
        print_colored(f"Warning: scripts directory not found at {scripts_dir}", Colors.YELLOW)
    
    # Change to backend directory
    os.chdir(backend_dir)
    
    # Create virtual environment
    venv_dir = backend_dir / "venv"
    
    if venv_dir.exists():
        print_colored("\nVirtual environment already exists. Skipping creation.", Colors.YELLOW)
    else:
        if not run_command(
            f"{sys.executable} -m venv venv",
            "Creating virtual environment"
        ):
            sys.exit(1)
    
    # Determine activation command and pip path
    if os_name == "Windows":
        activate_cmd = str(venv_dir / "Scripts" / "activate")
        pip_cmd = str(venv_dir / "Scripts" / "pip")
        python_cmd = str(venv_dir / "Scripts" / "python")
    else:
        activate_cmd = f"source {venv_dir / 'bin' / 'activate'}"
        pip_cmd = str(venv_dir / "bin" / "pip")
        python_cmd = str(venv_dir / "bin" / "python")
    
    # Upgrade pip
    if not run_command(
        f'"{pip_cmd}" install --upgrade pip',
        "Upgrading pip"
    ):
        print_colored("Warning: Failed to upgrade pip, continuing anyway...", Colors.YELLOW)
    
    # Check for requirements.txt
    requirements_file = backend_dir / "requirements.txt"
    
    if not requirements_file.exists():
        print_colored("\nrequirements.txt not found. Creating default...", Colors.YELLOW)
        requirements_content = """sklearn-crfsuite==0.3.6
scikit-learn>=1.0.0
pythainlp>=4.0.0
flask>=2.0.0
flask-cors>=3.0.10
pandas>=1.3.0
numpy>=1.21.0
python-dotenv>=0.19.0
"""
        requirements_file.write_text(requirements_content)
        print_colored("✓ requirements.txt created", Colors.GREEN)
    
    # Install dependencies
    if not run_command(
        f'"{pip_cmd}" install -r requirements.txt',
        "Installing dependencies"
    ):
        sys.exit(1)
    
    # Success message
    print_colored("\n" + "=" * 50, Colors.GREEN)
    print_colored("Setup Complete! 🎉", Colors.GREEN)
    print_colored("=" * 50, Colors.GREEN)
    
    print_colored("\nTo activate the environment:", Colors.BLUE)
    if os_name == "Windows":
        print_colored(f"  cd backend", Colors.YELLOW)
        print_colored(f"  venv\\Scripts\\activate", Colors.YELLOW)
        print_colored("  or in PowerShell:", Colors.BLUE)
        print_colored(f"  .\\venv\\Scripts\\Activate.ps1", Colors.YELLOW)
    else:
        print_colored(f"  cd backend", Colors.YELLOW)
        print_colored(f"  source venv/bin/activate", Colors.YELLOW)
    
    print_colored("\nTo run the inference script:", Colors.BLUE)
    print_colored("  python scripts/crf_mtu_inference.py", Colors.YELLOW)
    print()

if __name__ == "__main__":
    main()
