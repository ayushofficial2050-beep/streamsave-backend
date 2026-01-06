import os
from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import yt_dlp

app = Flask(__name__)
CORS(app)

# Custom User Agent (Android Phone)
custom_user_agent = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36'

@app.route('/')
def home():
    return "StreamSave Server is ON and Ready! 🟢"

@app.route('/analyze', methods=['POST'])
def analyze_video():
    data = request.json
    video_url = data.get('url')

    if not video_url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # MAGIC SETTINGS TO BYPASS YOUTUBE BLOCK
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best',
            'user_agent': custom_user_agent,
            'nocheckcertificate': True,
            # Ye line YouTube ko confuse karegi ki hum Android App hain
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            
            title = info.get('title', 'Unknown Title')
            thumbnail = info.get('thumbnail', '')
            duration = info.get('duration', 0)
            channel = info.get('uploader', 'Unknown Channel')
            
            # Duration String
            m, s = divmod(duration, 60)
            h, m = divmod(m, 60)
            duration_str = f'{h}:{m:02d}:{s:02d}' if h > 0 else f'{m}:{s:02d}'

            formats = []
            seen_qualities = set()

            for f in info.get('formats', []):
                resolution = f.get('height')
                if not resolution: continue
                
                res_str = f"{resolution}p"
                ext = f.get('ext', 'mp4')
                filesize = f.get('filesize') or f.get('filesize_approx')
                size_mb = f"{round(filesize / (1024 * 1024), 1)} MB" if filesize else "Unknown"
                
                # Redirect Link
                download_link = f"/download?url={video_url}&format_id={f['format_id']}"

                unique_key = f"{res_str}-{ext}"
                
                if unique_key not in seen_qualities and ext in ['mp4', 'webm']:
                    seen_qualities.add(unique_key)
                    formats.append({
                        "resolution": res_str,
                        "ext": ext,
                        "filesize": size_mb,
                        "download_url": download_link
                    })

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
        return jsonify({"error": str(e)}), 500

@app.route('/download', methods=['GET'])
def download_video():
    url = request.args.get('url')
    format_id = request.args.get('format_id')

    try:
        ydl_opts = {
            'format': format_id,
            'user_agent': custom_user_agent,
            'nocheckcertificate': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
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
        ydl_opts = {
            'format': 'bestaudio/best',
            'user_agent': custom_user_agent,
            'nocheckcertificate': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return redirect(info.get('url'))
    except Exception as e:
        return f"Error: {e}"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
