from flask import Flask, render_template, request, jsonify, make_response
import os
import uuid
import logging
import io 
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
# 2. YÜKLƏMƏ FUNKSİYASI (FİNAL HƏLL: GET/POST İcazəsi + Sabitlik)
# ----------------------------------------------------------------------

@app.route('/yukle', methods=['GET', 'POST']) 
def yukle():
    # Fayl yükləməni başlatmaq üçün POST sorğusu
    if request.method == 'POST':
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({"success": False, "message": "Link daxil edilməyib."}), 400

        random_filename = str(uuid.uuid4())
        filepath = os.path.join(DOWNLOAD_FOLDER, f"{random_filename}.mp4")

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
                ydl.download([url])

            logging.info(f"Video uğurla yükləndi: {filepath}")
            
            # Uğurlu Halda Yönləndirmə URL-ini göndəririk (JavaScript bunu gözləyir)
            return jsonify({"success": True, "download_url": request.base_url + "?filename=" + random_filename}), 200
            
        except Exception as e:
            logging.error(f"Server xətası: {e}")
            return jsonify({
                "success": False,
                "message": f"Daxili server xətası baş verdi. {e}"
            }), 500
            
        finally:
            # Fayl hələlik silinmir, GET müraciətini gözləyir.
            pass

    # Faylı göndərmək üçün GET sorğusu (window.location.href tərəfindən gəlir)
    elif request.method == 'GET':
        filename_uuid = request.args.get('filename')
        if not filename_uuid:
             return jsonify({"success": False, "message": "Fayl identifikasiyası tapılmadı."}), 400
             
        filepath = os.path.join(DOWNLOAD_FOLDER, f"{filename_uuid}.mp4")

        if not os.path.exists(filepath):
            return jsonify({"success": False, "message": "Yükləmə faylı artıq silinib və ya tapılmadı."}), 404

        try:
            file_size = os.path.getsize(filepath)
            
            with open(filepath, 'rb') as f:
                video_data = f.read()
                
            response = make_response(video_data)
            
            # Başlıqlar: Yükləmə Uğursuz Oldu xətasını həll edir
            response.headers['Content-Type'] = 'video/mp4'
            response.headers['Content-Disposition'] = 'attachment; filename="video.mp4"' # Sadə fayl adı
            response.headers['Content-Length'] = file_size
            
            if 'Transfer-Encoding' in response.headers:
                del response.headers['Transfer-Encoding']

            return response
            
        except Exception as e:
             return jsonify({"success": False, "message": f"Fayl ötürülməsi zamanı xəta: {e}"}), 500
             
        finally:
            # Fayl göndərildikdən sonra mütləq silinir
            if os.path.exists(filepath):
                os.remove(filepath)
                logging.info(f"Fayl silindi: {filepath}")
                
    return jsonify({"success": False, "message": "Metod keçərsizdir."}), 405


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port) 