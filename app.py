from flask import Flask, request, jsonify, Response
import requests
import time
import os
from urllib.parse import urlencode, urlparse

app = Flask(__name__)

# --------------------------------------------------------------------------------
# ⚠️ KRİTİK ƏMƏLİYYAT: VİDEO LİNKİNİ ƏLDƏ ETMƏK (SİZİN MÖVCUD KODUNUZ)
# --------------------------------------------------------------------------------
def get_tiktok_final_link(tiktok_url):
    """
    Bu funksiya sizin TikTok linkini watermarksız video linkinə çevirən 
    köhnə və işləyən MƏNTİQİNİZİ ehtiva etməlidir. 
    Zəhmət olmasa, bu funksiyanın daxilini öz kodunuzla doldurun.
    """
    # Xəta olmaması üçün müvəqqəti None qaytarılır.
    # Lütfən, bu funksiyanın içini öz kodunuzla əvəz edin!
    return None 

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
        # Video linkini sizin kodunuzla əldə edirik
        final_download_url = get_tiktok_final_link(tiktok_url)
        
        if not final_download_url:
             return jsonify({"success": False, "message": "Video linki tapılmadı."}), 404

        # KRİTİK HƏLL: Yükləməni bizim proxy endpointimizə yönləndiririk.
        encoded_link = urlencode({'link': final_download_url})
        download_proxy_url = f'/download_proxy?{encoded_link}' 

        return jsonify({"success": True, "download_url": download_proxy_url })

    except Exception as e:
        app.logger.error(f"Video yükləmə zamanı xəta: {e}")
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
        # Linkin keçərliyini yoxlamaq üçün fayla sorğu göndəririk
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
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8000), debug=True)