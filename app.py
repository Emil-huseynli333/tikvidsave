from flask import Flask, render_template, request, jsonify, send_file
import os
import uuid
import logging
from yt_dlp import YoutubeDL, DownloadError

# Loglama üçün tənzimləmə
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, template_folder='templates')

# Yükləmələrin saxlanılacağı qovluğu təyin et
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

@app.route('/')
def index():
    # Burada sizin index.html faylınızın məzmunu render edilir
    return render_template('index.html')

@app.route('/yukle', methods=['GET', 'POST']) 
def yukle():
    
    # POST Hissəsi (Yükləmənin Başlanması)
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
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Uğurlu Halda Yönləndirmə URL-ini göndəririk 
            return jsonify({"success": True, "download_url": request.base_url + "?filename=" + random_filename}), 200
            
        except Exception as e:
            logging.error(f"Server xətası: {e}")
            return jsonify({"success": False, "message": f"Daxili server xətası baş verdi. {e}"}), 500
            
        finally:
            pass

    # GET Hissəsi (Faylın Ötürülməsi) - Bütün başlıq uyğunsuzluqları burada həll edilir.
    elif request.method == 'GET':
        filename_uuid = request.args.get('filename')
        
        if not filename_uuid:
             return jsonify({"success": False, "message": "Fayl identifikasiyası tapılmadı."}), 400
             
        filepath = os.path.join(DOWNLOAD_FOLDER, f"{filename_uuid}.mp4")

        if not os.path.exists(filepath):
            return jsonify({"success": False, "message": "Yükləmə faylı artıq silinib və ya tapılmadı."}), 404

        try:
            
            # Flask-ın ən etibarlı fayl ötürmə funksiyası
            response = send_file(
                filepath,
                mimetype='video/mp4',
                as_attachment=True,
                download_name='video.mp4' 
            )
            
            # --- QƏTİ HƏLL BAŞLIQLARI (Android üçün kritikdir) ---
            response.headers['Content-Type'] = 'video/mp4'           # Mütləq MIME tipi təsdiqi
            response.headers['Accept-Ranges'] = 'bytes'              # Hissəli yükləməyə icazə
            response.headers['Connection'] = 'close'                 # Yükləmənin düzgün bağlanması üçün
            
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