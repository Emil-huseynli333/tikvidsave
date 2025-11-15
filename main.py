# app.py
from flask import Flask, request, jsonify, send_file
from yt_dlp import YoutubeDL
import os
import tempfile

app = Flask(__name__)

# Çox sadə bir CORS (Cross-Origin Resource Sharing) imkanı
# Lazım ola bilər ki, brauzer sizin frontend-dən backend-ə sorğu göndərə bilsin.
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

@app.route('/')
def index():
    return "Backend işləyir!"

@app.route('/yukle', methods=['POST'])
def download_tiktok():
    # 1. İstəkdən (request) linki almaq
    try:
        data = request.get_json()
        tiktok_url = data.get('url')
    except Exception as e:
        return jsonify({"message": "Yanlış giriş formatı"}), 400

    if not tiktok_url or 'tiktok.com' not in tiktok_url:
        return jsonify({"message": "Zəhmət olmasa düzgün TikTok linki daxil edin"}), 400

    # 2. Müvəqqəti fayl yerini təyin etmək
    # Yüklənəcək faylları müvəqqəti qovluqda saxlayacağıq.
    temp_dir = tempfile.mkdtemp()
    
    # yt-dlp konfiqurasiyası
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]', # MP4 formatını seç
        'outtmpl': os.path.join(temp_dir, 'video.%(ext)s'), # Fayl adını təyin et
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            # Video məlumatlarını əldə et
            info = ydl.extract_info(tiktok_url, download=False)
            
            # Əgər info yoxdursa və ya video tapılmırsa
            if not info:
                 return jsonify({"message": "Video məlumatları tapılmadı."}), 404
                 
            # Yükləməni icra et (fayl müvəqqəti qovluqda saxlanılır)
            ydl.download([tiktok_url])

            # Yüklənmiş faylın tam yolunu tapmaq (adətən video.mp4 olur)
            downloaded_file_path = os.path.join(temp_dir, "video.mp4")

            # 3. Faylı istifadəçiyə göndərmək
            if os.path.exists(downloaded_file_path):
                # Faylı istifadəçiyə göndər və brauzerin onu yükləməsini təmin et.
                response = send_file(downloaded_file_path, as_attachment=True, download_name='tiktok_video.mp4')
                
                # Fayl göndərildikdən sonra müvəqqəti qovluğu silin
                import shutil
                shutil.rmtree(temp_dir)
                
                return response

            else:
                 return jsonify({"message": "Video MP4 formatında yüklənə bilmədi."}), 500

    except Exception as e:
        # Bütün digər xətalar üçün (məsələn, linkin dəstəklənməməsi)
        return jsonify({"message": f"Server xətası: {str(e)}"}), 500

if __name__ == '__main__':
    # Layihəni debug rejimində işə salın
    app.run(debug=True)