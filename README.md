# TikTok Video/Audio Downloader

A Flask application that allows downloading TikTok videos and audio using yt-dlp.

## Features

- Download TikTok videos in MP4 format
- Extract audio from TikTok videos in MP3 format
- Automatic file cleanup
- Error handling and logging
- Production-ready configuration

## Requirements

- Python 3.8+
- FFmpeg (required for audio extraction)
- Other dependencies listed in `requirements.txt`

## Deployment on Render.com

1. Create a new Web Service on Render.com
2. Connect your GitHub repository
3. Configure the following settings:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Plan**: Choose appropriate plan (Free tier works for testing)

4. Add the following environment variables:
   - `PYTHON_VERSION`: `3.8` or higher
   - `PORT`: Will be set automatically by Render

5. Deploy the application

## Local Development

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the application:
   ```bash
   python app.py
   ```

## Important Notes

- The application automatically cleans up downloaded files older than 24 hours to ensure optimal performance and storage management.
- Logs are stored in the `logs` directory with rotation to help monitor and debug the application effectively.
- FFmpeg must be installed on the deployment server for audio extraction to work seamlessly. Ensure it is properly configured to avoid any issues during audio processing.
- The application is designed with user privacy in mind; no personal data is stored or shared.
- For best results, always use the latest version of the application and dependencies.
