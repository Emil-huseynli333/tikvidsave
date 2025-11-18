from flask import Flask, request, jsonify, Response, render_template
import requests
import time
import os
from urllib.parse import urlencode

app = Flask(__name__)

# --------------------------------------------------------------------------------
# KÖMƏKÇİ FUNKSİYA: TİKTOK VİDEO LİNKİNİ ƏLDƏ ETMƏK (SİZİN KÖHNƏ MƏNTİQİNİZ)
# --------------------------------------------------------------------------------
def get_tiktok_final_link(tiktok_url):
    """
    ⚠️ DİQQƏT: Bu funksiya HAL HAZIRDA İŞLƏMİR (None qaytarır).
    Lütfən, aşağıdakı 'return None' sətrinin yerinə sizin KÖHNƏ, İŞLƏYƏN 
    API sorğunuzu/link əldə etmə məntiqinizi daxil edin!
    """
    
    # SİZİN KÖHNƏ İŞLƏYƏN API KODUNUZU BURAYA YAPIŞDIRIN!
    
    return None 


# --------------------------------------------------------------------------------
# ENDPOINT 0: ƏSAS SƏHİFƏ
# --------------------------------------------------------------------------------
@app.route('/')
def index():
    # Flask-ın index.html-i göstərməsini təmin edir
    return render_template('index.html')


# --------------------------------------------------------------------------------
# ENDPOINT 1: /yukle (FRONTENDDƏN GƏLƏN SORĞU)
# --------------------------------------------------------------------------------
@app.route('/yukle', methods=['POST'])
def yukle_video():
    data = request.get_json(silent=True)
    tiktok_url = data.get('url')

    if not tiktok_url:
        return jsonify({"success": False, "message": "Link daxil edilməyib"}), 400

    try:
        final_download_url = get_tiktok_final_link(tiktok_url)
        
        if not final_download_url:
             # Əgər link tapılmazsa 404 qaytarırıq (artıq 500 xətası yoxdur)
             return jsonify({"success": False, "message": "Video linki tapılmadı."}), 404

        # KRİTİK HƏLL: Proxy vasitəsilə yükləmə (Android və İcazə xətasını həll edir)
        encoded_link = urlencode({'link': final_download_url})
        download_proxy_url = f'/download_proxy?{encoded_link}' 

        return jsonify({"success": True, "download_url": download_proxy_url })

    except Exception as e:
        app.logger.error(f"Video yükləmə zamanı gözlənilməz xəta: {e}")
        return jsonify({"success": False, "message": f"Server Xətası: {str(e)}"}), 500


# --------------------------------------------------------------------------------
# ENDPOINT 2: /download_proxy (YÜKLƏMƏ UĞURSUZLUĞUNU HƏLL EDİR)
# --------------------------------------------------------------------------------
@app.route('/download_proxy')
def download_proxy():
    final_url = request.args.get('link')

    if not final_url:
        return "Yükləmə linki tapılmadı.", 400

    try:
        # Faylı requests ilə alır və Response ilə ötürürük (Lokal silmə xətası yoxdur)
        response = requests.get(final_url, stream=True, timeout=30)
        response.raise_for_status() 

        # Fayl adı yaratmaq
        filename = f"tiktok_video_{int(time.time())}.mp4"

        # DÜZGÜN HEADERLƏR: Android DownloadManager üçün vacibdir
        headers = {
            "Content-Type": "video/mp4", 
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0" 
        }

        # Faylı birbaşa ötürürük
        return Response(response.iter_content(chunk_size=8192), headers=headers)

    except requests.exceptions.HTTPError as e:
        return f"Yükləmə linki keçərsizdir: {e.response.status_code}", 404
    except Exception as e:
        return f"Proxylama zamanı gözlənilməz xəta: {str(e)}", 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 5000), debug=True)