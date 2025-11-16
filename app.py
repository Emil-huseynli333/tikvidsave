from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import uuid
import logging

# Loglama üçün tənzimləmə
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, template_folder='templates')

# Yükləmələrin saxlanılacağı qovluğu təyin et
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# Baş səhifə
@app.route('/')
def index():
    return render_template('index.html')

# YENİ ƏLAVƏ EDİLƏN: Məxfilik Siyasəti üçün Route
@app.route('/privacy')
def privacy_policy():
    return render_template('privacy.html')

# YENİ ƏLAVƏ EDİLƏN: İstifadə Şərtləri üçün Route
@app.route('/terms')
def terms_of_use():
    return render_template('terms.html')

# Video Yükləmə Funksiyası
@app.route('/yukle', methods=['POST'])
def yukle():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({"success": False, "message": "Link daxil edilməyib."}), 400

    # Təsadüfi fayl adı yarat
    random_filename = str(uuid.uuid4())
    filepath = os.path.join(DOWNLOAD_FOLDER, f"{random_filename}.mp4")

    # yt-dlp ilə yükləmə tənzimləmələri
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': filepath,
        'merge_output_format': 'mp4',
        'noplaylist': True,
        'no_warnings': True,
        'skip_download': False,
    }

    try:
        logging.info(f"Video yüklənir: {url}")
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Video haqqında məlumatı çıxar
            info = ydl.extract_info(url, download=False)
            
            # Əgər canlı yayım deyilsə və ya məlumat yoxdursa
            if info.get('is_live') or info.get('filesize') is None:
                 raise Exception("Video məlumatı tapılmadı və ya canlı yayım formatında oldu.")

            # Videonu yüklə
            ydl.download([url])

        logging.info(f"Video uğurla yükləndi: {filepath}")
        
        # Yüklənmiş faylı brauzerə göndər
        return send_file(filepath, as_attachment=True, download_name='tiktok_video.mp4')

    except Exception as e:
        logging.error(f"Yükləmə xətası baş verdi: {e}")
        # Xəta baş verdikdə JSON formatında cavab qaytar
        return jsonify({
            "success": False,
            "message": f"TikTok videosunu yükləmək mümkün olmadı. (Server Bloklandı və ya link keçərsizdir: {e})"
        }), 500  # 500 daxili server xətası
    finally:
        # Faylı göndərdikdən sonra sil
        if os.path.exists(filepath):
            os.remove(filepath)
            logging.info(f"Fayl silindi: {filepath}")


if __name__ == '__main__':
    # Render-də istifadə olunan portu istifadə et
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)