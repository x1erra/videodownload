import yt_dlp
import threading
import asyncio
import os
from socket_manager import manager

class Downloader:
    def __init__(self):
        self.active_downloads = {}
        # Ensure downloads folder exists
        if not os.path.exists("downloads"):
            os.makedirs("downloads")

    def _progress_hook(self, d):
        # This runs in a thread, so we need to bridge to asyncio for the websocket
        # For simplicity, we might just fire-and-forget or use an event loop
        # But since we are in a thread, we can't await directly on the main loop easily without thread-safety.
        # Minimal data extraction
        if d['status'] == 'downloading':
            data = {
                'type': 'progress',
                'id': d.get('info_dict', {}).get('id', 'unknown'),
                'filename': d.get('filename'),
                'percent': d.get('_percent_str', '0%'),
                'speed': d.get('_speed_str', '0'),
                'eta': d.get('_eta_str', '0'),
                'status': 'downloading'
            }
            asyncio.run_coroutine_threadsafe(manager.broadcast(data), self.loop)
        
        elif d['status'] == 'finished':
            data = {
                'type': 'finished',
                'id': d.get('info_dict', {}).get('id', 'unknown'),
                'filename': d.get('filename'),
                'status': 'finished'
            }
            asyncio.run_coroutine_threadsafe(manager.broadcast(data), self.loop)

    def start_download(self, url: str, format_id: str = "mp4", quality: str = "best", loop=None):
        self.loop = loop
        thread = threading.Thread(target=self._download_task, args=(url, format_id, quality))
        thread.start()

    def _download_task(self, url, format_id, quality):
        # Default options
        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'progress_hooks': [self._progress_hook],
            'quiet': True,
            'no_warnings': True,
        }

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
             # Video Mode (MP4, Any, etc)
             # 1. Determine Quality Selector
             format_selector = 'bestvideo+bestaudio/best' # default
             
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

             # 2. Apply Container Constraint
             if format_id == 'mp4':
                 ydl_opts['merge_output_format'] = 'mp4'
             # 'any' leaves merge_output_format unset, preserving original container (mkv/webm)
        
        
        # Instagram/Twitter specific headers or cookies might be needed here
        # yt-dlp handles many automatically, but we can enhance it.
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first to get ID/Title immediately?
                # info = ydl.extract_info(url, download=False)
                # Broadcast "started"
                
                ydl.download([url])
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            # Broadcast error
            asyncio.run_coroutine_threadsafe(manager.broadcast({
                'type': 'error',
                'url': url,
                'error': str(e)
            }), self.loop)

downloader_service = Downloader()
