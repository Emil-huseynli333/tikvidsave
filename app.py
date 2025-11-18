from flask import Flask, render_template, request, jsonify, send_file # send_file İMPORT EDİLDİ
from flask import Flask, render_template, request, jsonify, send_file
import os
import uuid
import logging
@@ -7,30 +7,20 @@
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
    # POST Hissəsi (Yükləmənin Başlanması) - Dəyişmir, sabitdir.
if request.method == 'POST':
data = request.get_json()
url = data.get('url')
@@ -51,27 +41,19 @@ def yukle():
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
            return jsonify({"success": False, "message": f"Daxili server xətası baş verdi. {e}"}), 500

finally:
pass

    # Faylı göndərmək üçün GET sorğusu (Android DownloadManager üçün kritik)
    # GET Hissəsi (Faylın Ötürülməsi) - KRİTİK BAŞLIQ DÜZƏLİŞİ
elif request.method == 'GET':
filename_uuid = request.args.get('filename')

@@ -84,18 +66,19 @@ def yukle():
return jsonify({"success": False, "message": "Yükləmə faylı artıq silinib və ya tapılmadı."}), 404

try:
            logging.info(f"Fayl ötürülməsi başladıldı: {filepath}")

            # --- KRİTİK HƏLL: send_file fayl ötürülməsini və başlıqları stabil edir ---
            # send_file istifadə edilir
response = send_file(
filepath,
mimetype='video/mp4',
as_attachment=True,
download_name='video.mp4' 
)

            # 'Endirmə Uğursuz Oldu' xətasının qarşısını alır
            response.headers['Content-Disposition'] = 'attachment; filename="video.mp4"'
            # --- KRİTİK BAŞLIQLARIN ƏLAVƏSİ (DownloadManager Uyğunluğu) ---
            response.headers['Content-Type'] = 'video/mp4' 
            response.headers['Accept-Ranges'] = 'bytes'        # Faylın hissələrlə yüklənməsinə icazə verir
            response.headers['Connection'] = 'close'           # Əlaqəni düzgün bağlayır (Android üçün vacibdir)

return response
