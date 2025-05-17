from flask import Flask, render_template, request, jsonify
import requests
import yt_dlp
import os
import re
import subprocess

app = Flask(__name__)

def sanitize_filename(filename):
    # Replace invalid characters with underscores
    return re.sub(r'[^a-zA-Z0-9-_\.\s]', '_', filename).replace(' ', '_')

# Ensure yt_dlp is up-to-date
def update_yt_dlp():
    try:
        subprocess.run(['pip', 'install', '--upgrade', 'yt-dlp'], check=True)
    except Exception as e:
        print(f"Failed to update yt_dlp: {e}")

update_yt_dlp()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    tiktok_url = data.get('url')
    download_type = data.get('type', 'video')  # Default to video

    if not tiktok_url:
        return jsonify({'error': 'No URL provided'}), 400

    try:
        # Create a directory to store downloaded files
        download_dir = "downloads"
        os.makedirs(download_dir, exist_ok=True)

        # Store list of files before download
        files_before = set(os.listdir(download_dir))

        # Configure yt_dlp options
        ydl_opts = {
            'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
            'format': 'bestaudio/best' if download_type == 'audio' else 'mp4',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if download_type == 'audio' else [],
            'http_chunk_size': 1048576,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(tiktok_url, download=True)

        # Get list of new files after download
        files_after = set(os.listdir(download_dir))
        new_files = files_after - files_before

        if not new_files:
            return jsonify({'error': 'No file was downloaded'}), 500

        # Find the correct file based on download type
        if download_type == 'audio':
            # Look for new MP3 file
            mp3_files = [f for f in new_files if f.endswith('.mp3')]
            if not mp3_files:
                return jsonify({'error': 'MP3 file not found after conversion'}), 500
            file_path = os.path.join(download_dir, mp3_files[0])
        else:
            # For video, take the first new file
            file_path = os.path.join(download_dir, list(new_files)[0])

        # Verify if the file exists
        if not os.path.exists(file_path):
            return jsonify({'error': 'File not found after download'}), 500

        # Sanitize the filename
        sanitized_name = sanitize_filename(os.path.basename(file_path))
        static_dir = "static"
        os.makedirs(static_dir, exist_ok=True)
        static_file_path = os.path.join(static_dir, sanitized_name)

        # Ensure unique filename in static directory
        counter = 1
        while os.path.exists(static_file_path):
            base_name, ext = os.path.splitext(sanitized_name)
            sanitized_name = f"{base_name}_{counter}{ext}"
            static_file_path = os.path.join(static_dir, sanitized_name)
            counter += 1

        # Move the downloaded file to static directory
        try:
            os.rename(file_path, static_file_path)
        except FileNotFoundError:
            return jsonify({'error': 'Failed to move the file'}), 500

        # Return the download link
        return jsonify({'download_link': f'/{static_file_path}'})

    except Exception as e:
        print(f"Error during download: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
