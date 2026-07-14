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
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web'],
                    'skip': ['webpage']
                }
            },
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.youtube.com/'
            }
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # সেরা অডিও ট্র্যাকটি খুঁজে বের করা
            best_audio_url = None
            for f in info.get('formats', []):
                if f.get('acodec') != 'none' and f.get('vcodec') == 'none':
                    best_audio_url = f.get('url')
                    break
            
            formats_dict = {}
            
            for f in info.get('formats', []):
                # ভিডিও কোডেক না থাকলে বা ইউআরএল না থাকলে বাদ
                if not f.get('url') or f.get('vcodec') == 'none' or f.get('vcodec') is None:
                    continue
                
                height = f.get('height')
                if not height:
                    continue
                    
                quality_label = f"{height}p"
                has_audio = f.get('acodec') != 'none' and f.get('acodec') is not None
                
                # আমরা চাই প্রতিটি রেজোলিউশনের (যেমন 720p, 360p, 144p) বেস্ট লিংকটি রাখতে।
                # যদি এই রেজোলিউশনটি আগে না পেয়ে থাকি, অথবা নতুন পাওয়া লিংকটিতে অডিও+ভিডিও একসাথে থাকে (progressive), 
                # তাহলে সেটাকে প্রাধান্য দেবো।
                if quality_label not in formats_dict or (has_audio and not formats_dict[quality_label]['is_merged']):
                    formats_dict[quality_label] = {
                        "quality": quality_label,
                        "video_url": f.get('url'),
                        "audio_url": f.get('url') if has_audio else best_audio_url,
                        "is_merged": has_audio,
                        "ext": f.get('ext', 'mp4')
                    }
            
            # ডিকশনারি থেকে লিস্ট বানিয়ে রেজোলিউশন অনুযায়ী বড় থেকে ছোট সাজানো
            formats = list(formats_dict.values())
            formats.sort(key=lambda x: int(x['quality'].replace('p', '')), reverse=True)
            
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
