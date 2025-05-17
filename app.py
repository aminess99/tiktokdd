from flask import Flask, render_template, request, jsonify
import requests
import yt_dlp
import os
import re
import subprocess
import logging
from logging.handlers import RotatingFileHandler
import time
from datetime import datetime, timedelta
import shutil

app = Flask(__name__)

# Configure logging
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(
    handlers=[RotatingFileHandler('logs/app.log', maxBytes=100000, backupCount=3)],
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)

# Configure download and static directories
DOWNLOAD_DIR = "downloads"
STATIC_DIR = "static"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# File cleanup settings
MAX_FILE_AGE_HOURS = 24
CLEANUP_INTERVAL_HOURS = 1
last_cleanup_time = datetime.now()

def cleanup_old_files():
    """Remove files older than MAX_FILE_AGE_HOURS from download and static directories"""
    global last_cleanup_time
    current_time = datetime.now()
    
    if (current_time - last_cleanup_time).total_seconds() < CLEANUP_INTERVAL_HOURS * 3600:
        return

    logging.info("Starting file cleanup")
    cutoff_time = current_time - timedelta(hours=MAX_FILE_AGE_HOURS)
    
    for directory in [DOWNLOAD_DIR, STATIC_DIR]:
        try:
            for filename in os.listdir(directory):
                filepath = os.path.join(directory, filename)
                if os.path.isfile(filepath):
                    file_modified_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    if file_modified_time < cutoff_time:
                        os.remove(filepath)
                        logging.info(f"Removed old file: {filepath}")
        except Exception as e:
            logging.error(f"Error during cleanup in {directory}: {str(e)}")
    
    last_cleanup_time = current_time

def sanitize_filename(filename):
    # Replace invalid characters with underscores
    sanitized = re.sub(r'[^a-zA-Z0-9-_\.\s]', '_', filename)
    return sanitized.replace(' ', '_')[:200]  # Limit filename length

# Ensure yt_dlp is up-to-date
def update_yt_dlp():
    try:
        subprocess.run(['pip', 'install', '--upgrade', 'yt-dlp'], check=True)
        logging.info("Successfully updated yt-dlp")
    except Exception as e:
        logging.error(f"Failed to update yt-dlp: {str(e)}")

update_yt_dlp()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    cleanup_old_files()  # Cleanup old files before new download
    
    data = request.get_json()
    tiktok_url = data.get('url')
    download_type = data.get('type', 'video')

    if not tiktok_url:
        logging.warning("Download attempt with no URL provided")
        return jsonify({'error': 'No URL provided'}), 400

    try:
        logging.info(f"Starting download for URL: {tiktok_url}, type: {download_type}")
        
        # Store list of files before download
        files_before = set(os.listdir(DOWNLOAD_DIR))

        # Configure yt_dlp options with better error handling
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_DIR, '%(title)s.%(ext)s'),
            'format': 'bestaudio/best' if download_type == 'audio' else 'mp4',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if download_type == 'audio' else [],
            'http_chunk_size': 1048576,
            'quiet': True,
            'no_warnings': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logging.info("Extracting video info")
            info = ydl.extract_info(tiktok_url, download=True)
            logging.info(f"Successfully downloaded content: {info.get('title', 'Unknown title')}")

        # Get list of new files after download
        files_after = set(os.listdir(DOWNLOAD_DIR))
        new_files = files_after - files_before

        if not new_files:
            logging.error("No files were downloaded")
            return jsonify({'error': 'No file was downloaded'}), 500

        # Find the correct file based on download type
        if download_type == 'audio':
            mp3_files = [f for f in new_files if f.endswith('.mp3')]
            if not mp3_files:
                logging.error("MP3 file not found after conversion")
                return jsonify({'error': 'MP3 file not found after conversion'}), 500
            file_path = os.path.join(DOWNLOAD_DIR, mp3_files[0])
        else:
            file_path = os.path.join(DOWNLOAD_DIR, list(new_files)[0])

        if not os.path.exists(file_path):
            logging.error(f"Downloaded file not found: {file_path}")
            return jsonify({'error': 'File not found after download'}), 500

        # Sanitize and move the file
        sanitized_name = sanitize_filename(os.path.basename(file_path))
        static_file_path = os.path.join(STATIC_DIR, sanitized_name)

        # Ensure unique filename
        counter = 1
        base_name, ext = os.path.splitext(sanitized_name)
        while os.path.exists(static_file_path):
            sanitized_name = f"{base_name}_{counter}{ext}"
            static_file_path = os.path.join(STATIC_DIR, sanitized_name)
            counter += 1

        try:
            shutil.move(file_path, static_file_path)
            logging.info(f"File successfully moved to static directory: {static_file_path}")
        except Exception as e:
            logging.error(f"Failed to move file: {str(e)}")
            return jsonify({'error': 'Failed to move the file'}), 500

        return jsonify({'download_link': f'/{static_file_path}'})

    except Exception as e:
        error_message = str(e)
        logging.error(f"Error during download: {error_message}")
        return jsonify({'error': error_message}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    
    # Initial cleanup on startup
    cleanup_old_files()
    
    # Update yt-dlp on startup
    update_yt_dlp()
    
    app.run(host='0.0.0.0', port=port)
