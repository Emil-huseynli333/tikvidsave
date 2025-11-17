from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import uuid
import logging

# Loglama üçün tənzimləmə
logging.basicConfig(level=logging.INFO)

# Flask Tətbiqinin İcrası
# 'templates' qovluğunu şablonlar üçün təyin edir
app = Flask(__name__, template_folder='templates')

# Yükləmələrin saxlanılacağı qovluğu təyin et
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# ----------------------------------------------------------------------
# 1. TEMPLATE ROUTING (Qanuni səhifələr və index)
# ----------------------------------------------------------------------

# Baş səhifə
@app.route('/')
def index():
    return render_template('index.html')

# Məxfilik Siyasəti üçün Route
@app.route('/privacy')
def privacy_policy():
    return render_template('privacy.html')

# İstifadə Şərtləri üçün Route
@app.route('/terms')
def terms_of_use():
    return render_template('terms.html')

# ----------------------------------------------------------------------
# 2. ADS.TXT ROUTING (AdSense Təsdiqlənməsi üçün)
# ----------------------------------------------------------------------

@app.route('/ads.txt')
def serve_ads_txt():
    # Faylı repozitoriyanın əsas qovluğundan oxuyub göndərir.
    # Flask/Render-də ads.txt faylının birbaşa əlçatan olmasını təmin edir.
    try:
        return send_file('ads.txt', mimetype='text/plain')
    except Exception as e:
        logging.error(f"ads.txt faylı tapılmadı və ya göndərilmədi: {e}")
        return "Not Found", 404

# ----------------------------------------------------------------------
# 3. YÜKLƏMƏ FUNKSİYASI (MIME Type düzəlişi ilə)
# ----------------------------------------------------------------------

@app.route('/yukle', methods=['POST'])
def yukle():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({"success": False, "message": "Link daxil edilməyib."}), 400

    # Təsadüfi fayl adı yarat
    random_filename = str(uuid.uuid4())
    filepath = os.path.join(DOWNLOAD_FOLDER, f"{random_filename}.mp4")

    # yt-dlp ilə yükləmə tənzimləmələri (xəta verən postprocessor çıxarıldı)
    ydl_opts = {
        # Ən yaxşı MP4 video və audio formatını seçir
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
            # Əsas məlumatı çıxarır (Yükləmədən əvvəl)
            info = ydl.extract_info(url, download=False)
            
            if info.get('is_live'):
                 raise Exception("Canlı yayım linklərini dəstəkləmir.")
            
            # Videonu yüklə
            ydl.download([url])

        logging.info(f"Video uğurla yükləndi: {filepath}")
        
        # Yüklənmiş faylı brauzerə göndər
        # MIME Type dəqiqləşdirilməsi Android/WebView yükləmə problemini həll edir
        return send_file(
            filepath, 
            mimetype='video/mp4',
            as_attachment=True, 
            download_name='tiktok_video.mp4'
        )

    except Exception as e:
        logging.error(f"Yükləmə xətası baş verdi: {e}")
        # Xəta baş verdikdə JSON formatında cavab qaytar
        return jsonify({
            "success": False,
            "message": f"TikTok videosunu yükləmək mümkün olmadı. (Server Bloklandı və ya link keçərsizdir.)"
        }), 500
    finally:
        # Faylı göndərdikdən sonra sil
        if os.path.exists(filepath):
            os.remove(filepath)
            logging.info(f"Fayl silindi: {filepath}")


if __name__ == '__main__':
    # Render-də istifadə olunan portu istifadə et
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)