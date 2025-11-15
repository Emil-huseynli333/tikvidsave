# app.py
from flask import Flask, request, jsonify, send_file, render_template 
from yt_dlp import YoutubeDL
import os
import tempfile
import shutil

app = Flask(__name__)

# Bütün CORS (Domainlər Arası) Problemlərini Həll Edən Hissə
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

# -----------------
# 1. Frontend-i təqdim edən yol (index.html)
# -----------------
@app.route('/')
def index():
    # templates/index.html faylını göstərir
    return render_template('index.html') 

# -----------------
# 2. Yükləməni icra edən API yolu
# -----------------
@app.route('/yukle', methods=['POST'])
def download_tiktok():
    # 1. İstəkdən (request) linki almaq
    try:
        data = request.get_json()
        tiktok_url = data.get('url')
    except Exception:
        return jsonify({"message": "Yanlış giriş formatı (JSON tələb olunur)"}), 400

    if not tiktok_url or not isinstance(tiktok_url, str) or 'tiktok.com' not in tiktok_url:
        return jsonify({"message": "Zəhmət olmasa düzgün TikTok linki daxil edin"}), 400

    # 2. Müvəqqəti fayl yerini təyin etmək
    temp_dir = tempfile.mkdtemp()
    
    # yt-dlp konfiqurasiyası
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]', 
        'outtmpl': os.path.join(temp_dir, 'video.%(ext)s'), 
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30, 
        'add_header': [
            ('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36')
        ],
        # YENİ ƏLAVƏ: Bəzi məhdudiyyətli videolara kömək edə bilər
        'referer': 'https://www.tiktok.com/',
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # Yükləməni icra et
            ydl.download([tiktok_url])

            # Yüklənmiş faylın tam yolunu tapmaq
            downloaded_file_path = os.path.join(temp_dir, "video.mp4")
            
            # 3. Faylı istifadəçiyə göndərmək
            if os.path.exists(downloaded_file_path):
                response = send_file(
                    downloaded_file_path, 
                    as_attachment=True, 
                    download_name='tiktok_video.mp4',
                    mimetype='video/mp4'
                )
                # YENİ ƏLAVƏ: Fayl göndərildikdən sonra silinməni təmin edir
                @response.call_on_close
                def remove_temp_dir():
                    shutil.rmtree(temp_dir)
                    
                return response
            else:
# ...
                 return jsonify({"message": "Video MP4 formatında yüklənə bilmədi. (Serverdə emal xətası)"}), 500

    except Exception as e:
        return jsonify({"message": f"Server xətası: {str(e)}"}), 500

    

