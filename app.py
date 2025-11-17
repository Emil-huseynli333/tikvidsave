from flask import Flask, render_template, request, jsonify, Response
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
# 1. TEMPLATE ROUTING 
# ----------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')

# ----------------------------------------------------------------------
# 2. YÜKLƏMƏ FUNKSİYASI (FİNAL HƏLL: Streaming Generator)
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

        # --- FİNAL QƏTİ HƏLL: Faylı hissələrlə oxuyub axınla göndəririk ---
        
        def generate_chunks():
            # Faylı kiçik hissələrlə oxuyur və göndərir
            with open(filepath, 'rb') as f:
                chunk_size = 8192 # 8KB
                chunk = f.read(chunk_size)
                while chunk:
                    yield chunk
                    chunk = f.read(chunk_size)

        file_size = os.path.getsize(filepath)
        
        # Faylı Response obyektinə generator kimi ötürürük
        response = Response(generate_chunks(), mimetype='video/mp4')
        
        # Başlıqlar
        response.headers['Content-Disposition'] = 'attachment; filename="tiktok_video.mp4"'
        response.headers['Content-Length'] = file_size 
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        
        # Mütləq Transfer-Encoding-i silirik
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