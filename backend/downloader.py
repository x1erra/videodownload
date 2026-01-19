import yt_dlp
import threading
import asyncio
import os
import shutil
import time
import re
from socket_manager import manager

import uuid

def sanitize_filename(name):
    # Remove potentially dangerous characters and ensure it's not too long
    sanitized = re.sub(r'[\\/*?:"<>|]', '', name)
    return sanitized[:200]

class Downloader:
    def __init__(self):
        self.active_downloads = {}
        # Ensure folders exist
        for folder in ["downloads", "processing"]:
            if not os.path.exists(folder):
                os.makedirs(folder)

    async def start_download(self, url: str, format_id: str = "mp4", quality: str = "best", task_id: str = None, strict_mode: bool = False, split_chapters: bool = False, loop=None):
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
        
        self.loop = loop
        # Use provided ID or generate a new one
        if not task_id:
            task_id = str(uuid.uuid4())
        
        # Use default executor (ThreadPoolExecutor) to run blocking download
        loop.run_in_executor(None, self._download_task, task_id, url, format_id, quality, strict_mode, split_chapters)
        return task_id

    def _download_task(self, task_id, url, format_id, quality, strict_mode, split_chapters):
        # We use the ID as the temporary filename to avoid collisions and special char issues in paths
        
        # We need a progress hook that captures 'd' but also knows about 'task_id'
        def progress_hook(d):
             if d['status'] == 'downloading':
                data = {
                    'type': 'progress',
                    'id': task_id,
                    'filename': d.get('filename'), # This is the temp filename usually
                    'percent': d.get('_percent_str', '0%'),
                    'speed': d.get('_speed_str', '0'),
                    'eta': d.get('_eta_str', '0'),
                    'status': 'downloading'
                }
                asyncio.run_coroutine_threadsafe(manager.broadcast(data), self.loop)
        
        ydl_opts = {
            'outtmpl': f'processing/{task_id}.%(ext)s', # Use task_id for tracking temp file
            'progress_hooks': [progress_hook],
            'quiet': False,
            'no_warnings': False,
            'continuedl': True,
            'nocheckcertificate': True,
            'retries': 10,
            'fragment_retries': 10,
            'concurrent_fragment_downloads': 5, # Speed up HLS
            'noplaylist': strict_mode, # Strict Mode
            'split_chapters': split_chapters, # Split Chapters
        }

        if split_chapters:
             ydl_opts['force_keyframes_at_cuts'] = True # Ensure clean cuts for chapters

        if format_id == 'thumbnail':
            ydl_opts['writethumbnail'] = True
            ydl_opts['skip_download'] = True
        elif format_id in ['mp3', 'm4a', 'opus', 'wav', 'flac']:
            ydl_opts['format'] = 'bestaudio/best'
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': format_id,
                'preferredquality': '192',
            }]
        else:
             # Video Mode
             # For Twitch/HLS, sometimes bestvideo+bestaudio causes chunk issues
             # We will try to force a single format if possible or better merging
             format_selector = 'bestvideo+bestaudio/best'
             
             if quality == 'best':
                 format_selector = 'bestvideo+bestaudio/best'
             elif quality == 'best_ios':
                 format_selector = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
             elif quality == 'worst':
                 format_selector = 'worstvideo+worstaudio/worst'
             elif quality.endswith('p'):
                 height = quality[:-1]
                 format_selector = f'bestvideo[height<={height}]+bestaudio/best[height<={height}]'
             
             ydl_opts['format'] = format_selector
             ydl_opts['merge_output_format'] = 'mp4' if format_id == 'mp4' or format_id == 'any' else None
        
        
        # Instagram/Twitter specific headers or cookies might be needed here
        # yt-dlp handles many automatically, but we can enhance it.
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # 1. INITIALIZE & EXTRACT
                # Broadcast immediately
                asyncio.run_coroutine_threadsafe(manager.broadcast({
                    'type': 'progress',
                    'id': task_id,
                    'status': 'initializing',
                    'percent': '0%',
                    'speed': 'Connecting...',
                    'eta': 'Preparing...'
                }), self.loop)

                info = ydl.extract_info(url, download=False)
                # We don't use the video_id for the task ID anymore, but we can keep it for reference if needed
                title = info.get('title', 'video')
                
                # Update with title
                asyncio.run_coroutine_threadsafe(manager.broadcast({
                    'type': 'progress',
                    'id': task_id,
                    'filename': title,
                    'status': 'starting',
                    'percent': '0%',
                }), self.loop)

                # 2. DOWNLOAD (to processing folder)
                ydl.download([url])
                
                # 3. VERIFY & MOVE (Atomic)
                # Broadcast merging status
                asyncio.run_coroutine_threadsafe(manager.broadcast({
                    'type': 'progress',
                    'id': task_id,
                    'status': 'merging',
                    'percent': '99%',
                    'speed': 'Processing',
                    'eta': 'Finalizing...'
                }), self.loop)

                # Small sleep to let ffmpeg close descriptors
                time.sleep(2)

                # Find the actual resulting file
                # yt-dlp might have changed the ext during merge
                candidate_exts = [format_id if format_id != 'any' else 'mp4', 'mp4', 'mkv', 'webm', 'm4a', 'mp3', 'wav', 'jpg', 'webp']
                actual_file = None
                
                # Try the direct name first using task_id
                possible_paths = [
                    os.path.join("processing", f"{task_id}.{ext}") for ext in candidate_exts
                ]
                
                for path in possible_paths:
                    if os.path.exists(path):
                        actual_file = path
                        break
                
                if not actual_file:
                    raise Exception("Could not find downloaded file in processing directory")

                # Move to final location with sanitized title
                ext = actual_file.rsplit('.', 1)[-1]
                safe_title = sanitize_filename(title)
                final_path = os.path.join("downloads", f"{safe_title}.{ext}")
                
                # If file already exists, add timestamp to avoid collision
                if os.path.exists(final_path):
                    final_path = os.path.join("downloads", f"{safe_title}_{int(time.time())}.{ext}")

                shutil.move(actual_file, final_path)
                
                # Double check size for logging
                file_size = os.path.getsize(final_path)
                print(f"Success: {final_path} ({file_size} bytes)")
                
                # 4. FINISH
                final_filename = os.path.basename(final_path)
                asyncio.run_coroutine_threadsafe(manager.broadcast({
                    'type': 'finished',
                    'id': task_id,
                    'filename': final_filename,
                    'file_size': file_size,
                    'status': 'finished'
                }), self.loop)

        except Exception as e:
            print(f"Error downloading {url}: {e}")
            # Broadcast error
            asyncio.run_coroutine_threadsafe(manager.broadcast({
                'type': 'error',
                'url': url,
                'id': task_id,
                'error': str(e)
            }), self.loop)
    
downloader_service = Downloader()
