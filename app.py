from flask import Flask, render_template, request, jsonify, make_response
import os
import uuid
import logging
from yt_dlp import YoutubeDL, DownloadError

# Loglama üçün tənzimləmə (Xətaları izləmək üçün vacibdir)
logging.basicConfig(level=logging.INFO)

# Flask Tətbiqinin İcrası
app = Flask(__name__, template_folder='templates')

# Yükləmələrin saxlanılacağı qovluğu təyin et
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

# ----------------------------------------------------------------------
# 1. TEMPLATE ROUTING 
# ----------------------------------------------------------------------

@app.route('/')
def index():
    # Bu, sizin index.html faylınızı istifadə edir və dizayna toxunmur.
    return render_template('index.html')

# ----------------------------------------------------------------------
# 2. YÜKLƏMƏ FUNKSİYASI (SABİT VƏ XƏTASIZ VERSİYA)
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

    # yt-dlp ilə yükləmə tənzimləmələri (ən yaxşı mp4 formatı)
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
        
        # Faylı tam yükləyib bitirir
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        logging.info(f"Video uğurla yükləndi: {filepath}")
        
        # --- ƏN STABİL FAYL ÖTÜRMƏ METODU (make_response) ---
        
        file_size = os.path.getsize(filepath)
        
        with open(filepath, 'rb') as f:
            video_data = f.read()
            
        response = make_response(video_data)
        
        # Başlıqlar: Android DownloadManager-in işləməsi üçün kritikdir
        response.headers['Content-Type'] = 'video/mp4'
        response.headers['Content-Disposition'] = 'attachment; filename="tiktok_video.mp4"'
        response.headers['Content-Length'] = file_size
        
        # Xətalı Transfer-Encoding-i silirik (Serverlə əlaqə xətasının qarşısını alır)
        if 'Transfer-Encoding' in response.headers:
            del response.headers['Transfer-Encoding']

        return response

    except DownloadError as e:
        logging.error(f"Yükləmə xətası: {e}")
        return jsonify({
            "success": False,
            "message": "Video tapılmadı və ya yüklənmədi. Linki yoxlayın."
        }), 400
        
    except Exception as e:
        logging.error(f"Ümumi server xətası: {e}")
        return jsonify({
            "success": False,
            "message": f"Daxili server xətası baş verdi. (Logları yoxlayın: {e})"
        }), 500
        
    finally:
        # Fayl istifadə edildikdən dərhal sonra silinir
        if os.path.exists(filepath):
            os.remove(filepath)
            logging.info(f"Fayl silindi: {filepath}")


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)