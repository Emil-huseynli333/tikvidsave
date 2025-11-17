from flask import Flask, render_template, request, jsonify, send_file
import os
import uuid
import logging
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

# (Buradakı digər /privacy, /terms, /ads.txt routelarını dəyişməyin)

# ----------------------------------------------------------------------
# 2. YÜKLƏMƏ FUNKSİYASI (SON DÜZƏLİŞ)
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
            
            # Faylı diskinizə yükləyir
            ydl.download([url])

        logging.info(f"Video uğurla yükləndi: {filepath}")
        
        # --- QƏTİ HƏLL: send_file ilə bütün başlıqları düzgün ötürürük ---
        
        # Faylın ölçüsünü alır
        file_size = os.path.getsize(filepath)

        # Faylı göndəririk. add_header=False əvvəlki başlığı silir.
        response = send_file(
            filepath,
            mimetype='video/mp4',
            as_attachment=True,
            download_name='tiktok_video.mp4'
        )
        
        # --- ƏN KRİTİK DƏYİŞİKLİK: Yükləməyə mane olan başlıqları silir ---
        # Bu, Render/Heroku kimi xidmətlərin əlavə etdiyi başlığı silə bilər.
        # Əsas başlıqları yenidən təyin edirik.
        response.headers['Content-Disposition'] = f"attachment; filename=tiktok_video.mp4"
        response.headers['Content-Type'] = 'video/mp4'
        response.headers['Content-Length'] = os.path.getsize(filepath)
        
        # Flask-ın özünün və ya hosting-in yaratdığı Transfer-Encoding başlığını silin.
        if 'Transfer-Encoding' in response.headers:
             del response.headers['Transfer-Encoding']

        return response

    except DownloadError as e:
        # Xəta hallarında fayl silinməsin
        logging.error(f"Yükləmə (yt-dlp) xətası baş verdi: {e}")
        return jsonify({
            "success": False,
            "message": "TikTok videosunu yükləmək mümkün olmadı. (Server Bloklandı və ya link keçərsizdir.)"
        }), 500
    
    except Exception as e:
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