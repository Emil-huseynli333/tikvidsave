from flask import Flask, render_template, request, jsonify
import os
import uuid
import logging
from werkzeug.exceptions import HTTPException
from yt_dlp import YoutubeDL, DownloadError

# Loglama üçün tənzimləmə
logging.basicConfig(level=logging.INFO)

# Flask Tətbiqinin İcrası
app = Flask(__name__, template_folder='templates')

# Yükləmələrin saxlanılacağı qovluğu təyin et
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# ----------------------------------------------------------------------
# 1. TEMPLATE ROUTING (Qanuni səhifələr və index)
# ----------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/privacy')
def privacy_policy():
    return render_template('privacy.html')

@app.route('/terms')
def terms_of_use():
    return render_template('terms.html')

# ----------------------------------------------------------------------
# 2. ADS.TXT ROUTING (AdSense Təsdiqlənməsi üçün)
# ----------------------------------------------------------------------

@app.route('/ads.txt')
def serve_ads_txt():
    # Faylı repozitoriyanın əsas qovluğundan oxuyub göndərir.
    try:
        # Fayl oxumaq üçün send_from_directory istifadə etmək daha etibarlıdır
        from flask import send_from_directory
        return send_from_directory(os.getcwd(), 'ads.txt', mimetype='text/plain')
    except Exception as e:
        logging.error(f"ads.txt faylı tapılmadı və ya göndərilmədi: {e}")
        return "Not Found", 404

# ----------------------------------------------------------------------
# 3. YÜKLƏMƏ FUNKSİYASI (RESPONSE OBYEKTİ İLƏ DƏQİQ ÖTÜRMƏ)
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
        logging.info(f"Video yüklənmə sorğusu: {url}")
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if info.get('is_live'):
                 raise Exception("Canlı yayım linklərini dəstəkləmir.")
            
            ydl.download([url])

        logging.info(f"Video uğurla yükləndi: {filepath}")
        
        # --- QƏTİ HƏLL: Faylı birbaşa HTTP Response kimi ötürürük ---
        
        # Faylı oxuyub birbaşa Response yaradırıq. Bu, 302 Redirect-in qarşısını alır.
        with open(filepath, 'rb') as f:
            data = f.read()

        response = app.make_response(data)
        
        # MIME Type və Yükləmə Başlıqları
        response.headers['Content-Type'] = 'video/mp4'
        response.headers['Content-Disposition'] = 'attachment; filename="tiktok_video.mp4"'
        
        return response

    except DownloadError as e:
        # yt-dlp xətaları üçün
        logging.error(f"Yükləmə (yt-dlp) xətası baş verdi: {e}")
        return jsonify({
            "success": False,
            "message": "TikTok videosunu yükləmək mümkün olmadı. (Server Bloklandı və ya link keçərsizdir.)"
        }), 500
    
    except Exception as e:
        # Digər bütün xətalar üçün
        logging.error(f"Ümumi server xətası: {e}")
        return jsonify({
            "success": False,
            "message": f"Daxili server xətası baş verdi: {e}"
        }), 500
        
    finally:
        # Faylı göndərdikdən sonra sil
        if os.path.exists(filepath):
            os.remove(filepath)
            logging.info(f"Fayl silindi: {filepath}")


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)