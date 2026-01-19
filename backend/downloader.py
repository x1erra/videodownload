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
            # We don't broadcast "finished" here because it triggers for each fragment/stream.
            # Merging and post-processing happen after this.
            # We will broadcast completion at the end of the _download_task.
            pass

    def start_download(self, url: str, format_id: str = "mp4", quality: str = "best", loop=None):
        self.loop = loop
        thread = threading.Thread(target=self._download_task, args=(url, format_id, quality))
        thread.start()

    def _download_task(self, url, format_id, quality):
        # Default options
        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'progress_hooks': [self._progress_hook],
            'quiet': False,
            'no_warnings': False,
            'continuedl': True,
            'nocheckcertificate': True,
            'ignoreerrors': False, # Set to False to catch issues
            'retries': 10,
            'fragment_retries': 10,
            'concurrent_fragment_downloads': 5, # Speed up HLS
            'hls_use_mpegts': True, # Can help with HLS merging
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
                info = ydl.extract_info(url, download=False)
                video_id = info.get('id', 'unknown')
                title = info.get('title', 'video')
                
                asyncio.run_coroutine_threadsafe(manager.broadcast({
                    'type': 'progress',
                    'id': video_id,
                    'filename': title,
                    'status': 'initializing',
                    'percent': '0%',
                    'speed': 'Connecting...',
                    'eta': 'Preparing...'
                }), self.loop)

                # 2. DOWNLOAD
                ydl.download([url])
                
                # 3. POST-PROCESSING BLOCK
                # Twitch HLS merging can be slow and brittle on Pi
                asyncio.run_coroutine_threadsafe(manager.broadcast({
                    'type': 'progress',
                    'id': video_id,
                    'status': 'merging',
                    'percent': '99%',
                    'speed': 'Processing',
                    'eta': 'Finalizing File...'
                }), self.loop)

                # Wait for disk flush and potential ffmpeg cleanup
                import time
                time.sleep(10) 

                # Double check file exists and has size
                filename = ydl.prepare_filename(info)
                # If we merged to mp4, the extension might have changed
                if not os.path.exists(filename) and os.path.exists(filename.rsplit('.', 1)[0] + '.mp4'):
                    filename = filename.rsplit('.', 1)[0] + '.mp4'

                if os.path.exists(filename):
                    file_size = os.path.getsize(filename)
                    print(f"Download finished: {filename} ({file_size} bytes)")
                
                # 4. FINISH
                asyncio.run_coroutine_threadsafe(manager.broadcast({
                    'type': 'finished',
                    'id': video_id,
                    'status': 'finished'
                }), self.loop)
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            # Broadcast error
            asyncio.run_coroutine_threadsafe(manager.broadcast({
                'type': 'error',
                'url': url,
                'id': 'error-' + str(hash(url)),
                'error': str(e)
            }), self.loop)

downloader_service = Downloader()
