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
    # Pass the current loop to the downloader so it can schedule async callbacks
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.get_event_loop()
        
    print(f"Got loop: {loop}, starting thread...")
    downloader_service.start_download(request.url, request.format, request.quality, loop)
    print("Thread started, returning response.")
    return {"status": "started", "url": request.url}

@app.get("/api/downloads")
def get_downloads():
    # List files in downloads directory
    files = []
    for filename in os.listdir("downloads"):
        path = os.path.join("downloads", filename)
        if os.path.isfile(path):
            stat = os.stat(path)
            files.append({
                "filename": filename,
                "size": stat.st_size,
                "url": f"/files/{filename}"
            })
    return files

@app.delete("/api/downloads/{filename}")
def delete_download(filename: str):
    path = os.path.join("downloads", filename)
    if os.path.exists(path):
        os.remove(path)
        return {"status": "deleted", "filename": filename}
    raise HTTPException(status_code=404, detail="File not found")
