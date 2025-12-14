#!/usr/bin/env python3
"""
Cross-platform venv activation and dependency checker.
Works on Windows, Linux, and macOS.

Features:
    - Idempotent: Safe to run multiple times
    - Process cleanup: Kills existing Flask servers before starting new ones
    - Cross-platform: Works on all operating systems
    - Logging: All output logged to logs/activate-env.log

Usage:
    python activate-env.py              # Check/install dependencies
    python activate-env.py --server     # Setup and start Flask server
"""

import sys
import os
import subprocess
import platform
from pathlib import Path
import logging
from datetime import datetime

# Setup logging
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
log_file = LOG_DIR / "activate-env.log"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def get_venv_path():
    """Get the virtual environment path."""
    return Path(__file__).parent / ".venv"


def get_python_executable():
    """Get the Python executable in the venv."""
    venv_path = get_venv_path()
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def get_pip_executable():
    """Get the pip executable in the venv."""
    venv_path = get_venv_path()
    if platform.system() == "Windows":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"


def venv_exists():
    """Check if venv already exists."""
    venv_path = get_venv_path()
    return venv_path.exists() and (venv_path / "pyvenv.cfg").exists()


def create_venv():
    """Create virtual environment."""
    print("[INFO] Creating virtual environment...")
    venv_path = get_venv_path()
    try:
        subprocess.check_call([sys.executable, "-m", "venv", str(venv_path)])
        print(f"[OK] Virtual environment created at {venv_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to create venv: {e}")
        return False


def kill_flask_processes():
    """Kill any existing Flask server processes (idempotent)."""
    try:
        if platform.system() == "Windows":
            # Windows: Use taskkill to find and kill python processes running backend.py
            try:
                subprocess.run(
                    ['taskkill', '/F', '/IM', 'python.exe', '/FI', 'WINDOWTITLE eq *backend*'],
                    capture_output=True,
                    timeout=5
                )
                print("[OK] Cleaned up any existing Flask processes")
            except Exception:
                pass  # If no processes found, that's fine
        else:
            # Linux/macOS: Use pkill to find and kill Python processes running backend.py
            try:
                subprocess.run(
                    ['pkill', '-f', 'backend.py'],
                    capture_output=True,
                    timeout=5
                )
                print("[OK] Cleaned up any existing Flask processes")
            except Exception:
                pass  # If no processes found, that's fine
    except Exception as e:
        print(f"[WARN] Could not clean up processes: {e}")


def check_and_install_requirements():
    """Check requirements.txt and install missing packages."""
    import json
    
    req_file = Path(__file__).parent / "requirements.txt"
    
    if not req_file.exists():
        print("[WARN] requirements.txt not found")
        return True
    
    python_exe = get_python_executable()
    
    if not python_exe.exists():
        print(f"[ERROR] python not found at {python_exe}")
        return False
    
    print(f"[INFO] Checking dependencies from {req_file}...")
    
    try:
        # Skip pip version check - it's too slow (makes network calls to PyPI)
        # Pip in venv is fresh enough and doesn't need frequent upgrades
        
        # Check what's already installed
        print("[INFO] Checking installed packages...")
        result = subprocess.run(
            [str(python_exe), "-m", "pip", "list", "--format=json"],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        installed_packages = {}
        if result.returncode == 0:
            try:
                pkg_list = json.loads(result.stdout)
                installed_packages = {pkg['name'].lower(): pkg['version'] for pkg in pkg_list}
                print(f"   Found {len(installed_packages)} installed package(s)")
            except json.JSONDecodeError as je:
                print(f"[ERROR] Could not parse installed packages: {je}")
                print(f"   pip output: {result.stdout[:200]}")
                return False
        else:
            print(f"[ERROR] Could not list installed packages: {result.stderr}")
            return False
        
        # Read requirements
        with open(req_file) as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not requirements:
            print("[WARN] No requirements found in requirements.txt")
            return True
        
        # Parse requirement names
        missing = []
        for req in requirements:
            # Extract package name (before ==, >=, <=, etc.)
            pkg_name = req.split('==')[0].split('>=')[0].split('<=')[0].split('>')[0].split('<')[0].strip().lower()
            
            if not pkg_name:
                print(f"[WARN] Could not parse package name from: {req}")
                continue
            
            if pkg_name not in installed_packages:
                missing.append(req)
        
        if missing:
            pkg_names = ', '.join([m.split('==')[0].split('>=')[0].split('<=')[0].strip() for m in missing])
            print(f"[INFO] Installing {len(missing)} missing package(s): {pkg_names}")
            subprocess.check_call([str(python_exe), "-m", "pip", "install"] + missing)
            print(f"[OK] Installed {len(missing)} package(s)")
        else:
            print("[OK] All required packages are already installed")
        
        print("[OK] All dependencies satisfied")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install dependencies: {e}")
        print(f"   Return code: {e.returncode}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error during dependency installation: {e}")
        return False


def print_activation_instructions():
    """Print instructions for activating the venv."""
    venv_path = get_venv_path()
    
    print("\n" + "=" * 70)
    print("[OK] ENVIRONMENT READY")
    print("=" * 70)
    
    if platform.system() == "Windows":
        activate_cmd = str(venv_path / "Scripts" / "Activate.ps1")
        print(f"\n[INFO] To activate the venv in PowerShell, run:")
        print(f"   & \"{activate_cmd}\"")
        print(f"\n[INFO] Or in cmd.exe, run:")
        print(f"   {venv_path / 'Scripts' / 'activate.bat'}")
    else:
        activate_cmd = f"source {venv_path / 'bin' / 'activate'}"
        print(f"\n[INFO] To activate the venv, run:")
        print(f"   {activate_cmd}")
    
    print(f"\n[INFO] To start the Flask server:")
    print(f"   python backend.py")
    print("\n" + "=" * 70)


def start_server():
    """Start the Flask server (idempotent - kills existing processes first)."""
    print("\n[INFO] Starting Flask server...")
    
    # Kill any existing processes
    kill_flask_processes()
    
    python_exe = get_python_executable()
    backend_file = Path(__file__).parent / "backend.py"
    
    try:
        subprocess.call([str(python_exe), str(backend_file)])
    except KeyboardInterrupt:
        print("\n\n[INFO] Server stopped by user")
    except Exception as e:
        print(f"[ERROR] Failed to start server: {e}")


def main():
    """Main setup function."""
    print("=" * 70)
    print("DnD Character Sheet - Environment Setup")
    print("=" * 70)
    logger.info("="*70)
    logger.info("DnD Character Sheet - Environment Setup")
    logger.info("="*70)
    
    start_server_after = "--server" in sys.argv
    
    # Step 1: Create venv if it doesn't exist
    if not venv_exists():
        if not create_venv():
            sys.exit(1)
    else:
        print(f"[OK] Virtual environment already exists at {get_venv_path()}")
    
    # Step 2: Install/check dependencies
    if not check_and_install_requirements():
        sys.exit(1)
    
    # Step 3: Print activation instructions
    print_activation_instructions()
    
    # Step 4: Optionally start server
    if start_server_after:
        start_server()


if __name__ == "__main__":
    main()
