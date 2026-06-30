import os
import subprocess
import sys

def build() -> None:
    """Builds frontend static assets and compiles the single-file backend executable."""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_dir = os.path.join(root, "frontend")
    backend_dir = os.path.join(root, "backend")

    # 1. Compile React Frontend Assets
    print("Building frontend dashboard static assets...")
    try:
        subprocess.run("npm run build", shell=True, cwd=frontend_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Frontend build failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

    # 2. Run PyInstaller Bundler
    print("Compiling single-file backend executable via PyInstaller...")
    # Locate virtualenv pyinstaller path
    pyinstaller_path = os.path.join(backend_dir, ".venv", "Scripts", "pyinstaller.exe")
    if not os.path.exists(pyinstaller_path):
        pyinstaller_path = "pyinstaller"

    cmd = f'"{pyinstaller_path}" aigateway.spec'
    try:
        subprocess.run(cmd, shell=True, cwd=backend_dir, check=True)
        print("Packaging successfully finished! Binary is located at backend/dist/aigateway.exe")
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller compilation failed: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    build()
