from flask import Flask, render_template, request, jsonify, send_file # send_file İMPORT EDİLDİ
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
# 2. YÜKLƏMƏ FUNKSİYASI (FİNAL QƏTİ HƏLL: send_file)
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
            
            # Uğurlu Halda Yönləndirmə URL-ini göndəririk 
            return jsonify({"success": True, "download_url": request.base_url + "?filename=" + random_filename}), 200
            
        except Exception as e:
            logging.error(f"Server xətası: {e}")
            return jsonify({
                "success": False,
                "message": f"Daxili server xətası baş verdi. {e}"
            }), 500
            
        finally:
            pass

    # Faylı göndərmək üçün GET sorğusu (Android DownloadManager üçün kritik)
    elif request.method == 'GET':
        filename_uuid = request.args.get('filename')
        
        if not filename_uuid:
             return jsonify({"success": False, "message": "Fayl identifikasiyası tapılmadı."}), 400
             
        filepath = os.path.join(DOWNLOAD_FOLDER, f"{filename_uuid}.mp4")

        if not os.path.exists(filepath):
            return jsonify({"success": False, "message": "Yükləmə faylı artıq silinib və ya tapılmadı."}), 404

        try:
            logging.info(f"Fayl ötürülməsi başladıldı: {filepath}")
            
            # --- KRİTİK HƏLL: send_file fayl ötürülməsini və başlıqları stabil edir ---
            response = send_file(
                filepath,
                mimetype='video/mp4',
                as_attachment=True,
                download_name='video.mp4' 
            )
            
            # 'Endirmə Uğursuz Oldu' xətasının qarşısını alır
            response.headers['Content-Disposition'] = 'attachment; filename="video.mp4"'
            
            return response
            
        except Exception as e:
             logging.error(f"Fayl ötürülməsi zamanı xəta: {e}")
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