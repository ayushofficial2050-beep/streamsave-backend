import os
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
# Allow Frontend to talk to Backend
CORS(app)

@app.route('/')
def home():
    return "StreamSave Server is ON! 🟢 (iOS Mode)"

@app.route('/analyze', methods=['POST'])
def analyze_video():
    data = request.json
    video_url = data.get('url')

    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # --- iOS TRICK SETTINGS ---
        # Ye settings YouTube ko force karengi ki wo hame iPhone samjhe
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            # Main Magic Line: Use iOS Client
            'extractor_args': {'youtube': {'player_client': ['ios']}},
            'nocheckcertificate': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            # 1. Basic Info Extraction
            title = info.get('title', 'Unknown Title')
            thumbnail = info.get('thumbnail', '')
            duration = info.get('duration', 0)
            channel = info.get('uploader', 'Unknown Channel')
            
            # 2. Duration Formatting
            m, s = divmod(duration, 60)
            h, m = divmod(m, 60)
            duration_str = f'{h}:{m:02d}:{s:02d}' if h > 0 else f'{m}:{s:02d}'

            # 3. Formats Processing
            formats = []
            seen_qualities = set()

            for f in info.get('formats', []):
                resolution = f.get('height')
                if not resolution: continue
                
                res_str = f"{resolution}p"
                ext = f.get('ext', 'mp4')
                
                # Calculate Size
                filesize = f.get('filesize') or f.get('filesize_approx')
                size_mb = f"{round(filesize / (1024 * 1024), 1)} MB" if filesize else "Unknown"
                
                # Create Redirect Link
                download_link = f"/download?url={video_url}&format_id={f['format_id']}"
                unique_key = f"{res_str}-{ext}"
                
                # Filter Logic: Keep unique MP4/WEBM
                if unique_key not in seen_qualities and ext in ['mp4', 'webm']:
                    seen_qualities.add(unique_key)
                    formats.append({
                        "resolution": res_str,
                        "ext": ext,
                        "filesize": size_mb,
                        "download_url": download_link
                    })

            # Sort High Quality First
            formats.sort(key=lambda x: int(x['resolution'].replace('p', '')), reverse=True)

            return jsonify({
                "title": title,
                "thumbnail": thumbnail,
                "channel": channel,
                "duration_seconds": duration,
                "duration_string": duration_str,
                "formats": formats
            })

    except Exception as e:
        # Send exact error to Frontend
        return jsonify({"error": str(e)}), 500

@app.route('/download', methods=['GET'])
def download_video():
    url = request.args.get('url')
    format_id = request.args.get('format_id')

    try:
        # Same iOS settings for download redirect
        ydl_opts = {
            'format': format_id,
            'extractor_args': {'youtube': {'player_client': ['ios']}},
            'nocheckcertificate': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return redirect(info.get('url'))
    except Exception as e:
        return f"Error: {e}"

@app.route('/download_audio', methods=['GET'])
def download_audio():
    url = request.args.get('url')
    try:
        # Same iOS settings for audio
        ydl_opts = {
            'format': 'bestaudio/best',
            'extractor_args': {'youtube': {'player_client': ['ios']}},
            'nocheckcertificate': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return redirect(info.get('url'))
    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
