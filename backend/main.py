from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import asyncio
import os
import shutil
from typing import List

from socket_manager import manager
from downloader import downloader_service

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure downloads directory exists
if not os.path.exists("downloads"):
    os.makedirs("downloads")

# Mount downloads to serve files
app.mount("/files", StaticFiles(directory="downloads"), name="files")

class DownloadRequest(BaseModel):
    url: str
    format: str = "mp4"
    quality: str = "best"
    
@app.get("/")
def read_root():
    return {"status": "OurTube Backend Running"}

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/api/downloads")
async def start_download(request: DownloadRequest):
    print(f"Received download request: {request.url}")
    # Start download in background executor
    task_id = await downloader_service.start_download(request.url, request.format, request.quality)
    print(f"Download scheduled with ID {task_id}, returning response.")
    return {"status": "started", "url": request.url, "id": task_id}




import re

def sanitize_filename(name: str) -> str:
    # Remove potentially dangerous characters and ensure it's not too long
    # This removes \ / : * ? " < > | and any control characters
    sanitized = re.sub(r'[\\/*?:"<>|]', '', name)
    # Also prevent .. entirely just in case
    sanitized = sanitized.replace('..', '')
    return sanitized

@app.delete("/api/downloads/{filename}")
def delete_download(filename: str):
    # 1. Sanitize the input filename
    safe_filename = sanitize_filename(filename)
    
    # 2. Reject if the filename was significantly altered (implies malicious intent or invalid chars)
    # Alternatively, we could just use the safe_filename, but rejecting avoids ambiguity.
    # For now, let's just ensure we only operate on the safe name.
    
    downloads_dir = os.path.abspath("downloads")
    target_path = os.path.abspath(os.path.join(downloads_dir, safe_filename))
    
    # 3. Verify path is actually inside downloads directory
    if not target_path.startswith(downloads_dir):
        # This should technically be impossible due to sanitize_filename removing slashes,
        # but it's a critical second layer of defense (defense in depth).
        print(f"Security Alert: Attempted path traversal with {filename}")
        raise HTTPException(status_code=400, detail="Invalid filename")

    if os.path.exists(target_path):
        os.remove(target_path)
        return {"status": "deleted", "filename": safe_filename}
        
    raise HTTPException(status_code=404, detail="File not found")
