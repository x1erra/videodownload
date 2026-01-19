import os

def test_vulnerability():
    base_dir = os.path.abspath("downloads")
    # Simulate user input
    filename = "../vulnerable_file.txt" 
    
    # Current Logic
    path = os.path.join("downloads", filename)
    absolute_path = os.path.abspath(path)
    
    print(f"Base Directory: {base_dir}")
    print(f"Malicious Input: {filename}")
    print(f"Resolved Path: {absolute_path}")
    
    if not absolute_path.startswith(base_dir):
        print("VULNERABILITY CONFIRMED: Path resolves outside of downloads directory!")
    else:
        print("Path seems safe.")

if __name__ == "__main__":
    if not os.path.exists("downloads"):
        os.makedirs("downloads")
    test_vulnerability()
