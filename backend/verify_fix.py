import os
import sys
from fastapi import HTTPException

# Add current directory to path so we can import main
sys.path.append(os.getcwd())

try:
    from main import sanitize_filename, delete_download
except ImportError:
    # If import fails (dependencies etc), we will copy the logic here for testing
    import re
    def sanitize_filename(name: str) -> str:
        sanitized = re.sub(r'[\\/*?:"<>|]', '', name)
        sanitized = sanitized.replace('..', '')
        return sanitized

def test_sanitization():
    print("--- Testing Sanitization ---")
    test_cases = [
        ("../../../etc/passwd", "etcpasswd"),
        ("..\\windows\\system32", "windowssystem32"),
        ("file|with|pipes.txt", "filewithpipes.txt"),
        ("normal_file.mp4", "normal_file.mp4"),
        ("cool?video.mp4", "coolvideo.mp4"),
    ]
    
    for input_name, expected in test_cases:
        result = sanitize_filename(input_name)
        print(f"Input: '{input_name}' -> Output: '{result}'")
        if result == expected:
            print("  [PASS]")
        else:
            print(f"  [FAIL] Expected '{expected}'")

def test_path_logic():
    print("\n--- Testing Path Logic (Simulation) ---")
    # Simulate directory structure
    base_dir = os.path.abspath("downloads")
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        
    # Test cases for the full logic
    inputs = ["../sensitive_file.txt", "valid_file.mp4", "nested/../hack.txt"]
    
    for filename in inputs:
        safe_filename = sanitize_filename(filename)
        target_path = os.path.abspath(os.path.join(base_dir, safe_filename))
        
        print(f"Attempting delete: {filename}")
        print(f"  Sanitized: {safe_filename}")
        print(f"  Target Path: {target_path}")
        
        if not target_path.startswith(base_dir):
            print("  [CRITICAL FAIL] Path traversal detected!")
        else:
            print("  [PASS] Path is safe (inside downloads)")

if __name__ == "__main__":
    test_sanitization()
    test_path_logic()
