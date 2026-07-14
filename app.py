from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import yt_dlp
import os

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)  # CORS সচল রাখা হলো

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
            
            formats = []
            seen_resolutions = set()
            
            # সব ফরম্যাট লুপ করে চেক করা হচ্ছে
            for f in info.get('formats', []):
                # শর্ত: ভিডিও ট্র্যাক থাকতে হবে এবং অডিও ট্র্যাকও থাকতে হবে (acodec ও vcodec কোনোটাই 'none' হতে পারবে না)
                if f.get('url') and f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    
                    # রেজুলেশনের নাম সেট করা (যেমন: 720p বা 360p)
                    quality = f.get('format_note') or f.get('resolution') or 'Unknown'
                    
                    # ডুপ্লিকেট রেজুলেশন বাদ দেওয়া হচ্ছে
                    if quality not in seen_resolutions:
                        seen_resolutions.add(quality)
                        formats.append({
                            "quality": quality,
                            "url": f.get('url'),
                            "ext": f.get('ext', 'mp4')
                        })
            
            # ভালো কোয়ালিটি উপরে দেখানোর জন্য রিভার্স করা হলো
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
