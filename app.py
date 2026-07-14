from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

@app.route('/index.html')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/info')
def get_video_info():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "url প্যারামিটার দাও"}), 400
    
    try:
        cookie_path = 'cookies.txt'
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        if os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # সেরা অডিও ট্র্যাকটি খুঁজে বের করা
            best_audio_url = None
            for f in info.get('formats', []):
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    best_audio_url = f.get('url')
                    break
            
            formats = []
            seen_resolutions = set()
            
            for f in info.get('formats', []):
                if f.get('url') and f.get('vcodec') != 'none':
                    quality = f.get('format_note') or f.get('resolution') or 'Unknown'
                    
                    if quality not in seen_resolutions and 'audio only' not in quality.lower():
                        seen_resolutions.add(quality)
                        
                        # যদি প্রোগ্রেসিভ ফরম্যাট হয় (আগে থেকেই অডিও আছে) তবে সেটার নিজস্ব অডিও থাকবে
                        # আর যদি অডিও না থাকে (acodec == 'none'), তবে আমাদের খুঁজে পাওয়া সেরা অডিওর লিংকটি জুড়ে দেব
                        has_audio = f.get('acodec') != 'none'
                        
                        formats.append({
                            "quality": quality,
                            "video_url": f.get('url'),
                            "audio_url": f.get('url') if has_audio else best_audio_url,
                            "is_merged": has_audio,
                            "ext": f.get('ext', 'mp4')
                        })
            
            formats.reverse()
            
            return jsonify({
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
                "formats": formats
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
