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
        # কুকিজ ফাইলের পাথ নির্ধারণ করা হচ্ছে
        cookie_path = 'cookies.txt'
        
        # অডিও ও ভিডিওসহ সেরা কোয়ালিটির কম্বাইন্ড ফরম্যাট খোঁজার কনফিগারেশন
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'format': 'best[ext=mp4]/best', # অডিও+ভিডিও সহ বেস্ট mp4
        }
        
        # যদি cookies.txt ফাইলটি প্রজেক্টে থাকে, তবে সেটি লোড করবে (আইপি ব্লক এড়াতে)
        if os.path.exists(cookie_path):
            ydl_opts['cookiefile'] = cookie_path
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # সরাসরি ভিডিওর ফাইনাল ডাউনলোড লিংকটি নেওয়া হচ্ছে
            direct_url = info.get('url')
            
            if not direct_url:
                return jsonify({"error": "ডাইরেক্ট লিংক পাওয়া যায়নি"}), 404
            
            return jsonify({
                "title": info.get('title'),
                "thumbnail": info.get('thumbnail'),
                "duration": info.get('duration'),
                "url": direct_url  # ফ্রন্টএন্ডের জন্য সরাসরি ভিডিও ইউআরএল
            })
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
