
import asyncio
import json
import sys
import urllib.request
import urllib.error
from websockets.client import connect

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
RESET = "\033[0m"

async def verify_fix():
    print("Starting verification of privacy fix...")
    
    url = "http://localhost:8000/api/downloads"
    payload = json.dumps({"url": "https://www.youtube.com/watch?v=BaW_jenozKc", "quality": "worst", "format": "mp3"}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})

    # 1. Start Download
    print("1. Sending download request...")
    task_id = None
    try:
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                print(f"{RED}Failed to start download: {response.status}{RESET}")
                return
            
            data = json.loads(response.read().decode('utf-8'))
            task_id = data.get("id")
            
            if not task_id:
                print(f"{RED}FAIL: No 'id' returned in start_download response.{RESET}")
                print(f"Response: {data}")
                return
            
            print(f"{GREEN}PASS: Received task ID: {task_id}{RESET}")
    except urllib.error.URLError as e:
         print(f"{RED}FAIL: Could not connect to API. Is backend running? {e}{RESET}")
         return

    # 2. Monitor WebSocket
    print("2. Connecting to WebSocket to verify events use this ID...")
    try:
        async with connect("ws://localhost:8000/ws") as websocket:
            print("Connected to WS. Waiting for events...")
            
            timeout = 10 
            start_time = asyncio.get_event_loop().time()
            
            found_progress = False
            
            while (asyncio.get_event_loop().time() - start_time) < timeout:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    data = json.loads(message)
                    event_id = data.get("id")
                    event_type = data.get("type")
                    
                    if event_id == task_id:
                        print(f"{GREEN}PASS: Received '{event_type}' event for correct ID: {event_id}{RESET}")
                        found_progress = True
                        break
                    else:
                        print(f"Received event for ID {event_id} (ignoring if not match)")
                            
                except asyncio.TimeoutError:
                    continue
            
            if found_progress:
                print(f"{GREEN}SUCCESS: verification passed. Backend is using unique IDs.{RESET}")
            else:
                print(f"{RED}FAIL: Did not receive any events for task ID {task_id} within timeout.{RESET}")

    except Exception as e:
        print(f"{RED}FAIL: WebSocket error: {e}{RESET}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(verify_fix())
