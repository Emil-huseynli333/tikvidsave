from flask import Flask, request, jsonify, Response
import requests
import time
import os
from urllib.parse import urlencode, urlparse
# yt-dlp kitabxanasını idxal edirik
import yt_dlp 

app = Flask(__name__)

# --------------------------------------------------------------------------------
# KÖMƏKÇİ FUNKSİYA: TİKTOK VİDEO LİNKİNİ ƏLDƏ ETMƏK (YT-DLP İLƏ)
# --------------------------------------------------------------------------------
def get_tiktok_final_link(tiktok_url):
    """
    yt-dlp istifadə edərək video linkini birbaşa əldə edir.
    """
    ydl_opts = {
        'format': 'best',
        'noplaylist': True,
        'quiet': True,
        'no_warnings': True,
        'skip_download': True, # Faylı yükləmədən yalnız məlumatı (linki) almaq
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Metadata əldə edirik
            info_dict = ydl.extract_info(tiktok_url, download=False)
            
            # Ən yaxşı linki əldə edirik (watermarksız versiya adətən ən yaxşı formatdır)
            # Bu, birbaşa CDN linkini qaytarır.
            final_download_url = info_dict['url']
            return final_download_url

    except Exception as e:
        # Hər hansı bir xəta zamanı (məsələn, link silinib)
        app.logger.error(f"yt-dlp xətası: {e}")
        return None 

# --------------------------------------------------------------------------------
# ENDPOINT 1: /yukle (FRONTENDDƏN SORĞUNU QƏBUL EDİR)
# --------------------------------------------------------------------------------
@app.route('/yukle', methods=['POST'])
def yukle_video():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"success": False, "message": "Göstərilən formatda JSON məlumatı tapılmadı."}), 400
        
    tiktok_url = data.get('url')

    if not tiktok_url:
        return jsonify({"success": False, "message": "Zəhmət olmasa, TikTok linkini daxil edin."}), 400

    try:
        # 1. Final video linkini əldə edirik (Yeni yt-dlp funksiyamızla)
        final_download_url = get_tiktok_final_link(tiktok_url)
        
        if not final_download_url:
             return jsonify({"success": False, "message": "Video linki tapılmadı və ya video silinib."}), 404

        # 2. KRİTİK HƏLL: Linki özümüzün proxy endpointimizə yönləndiririk.
        encoded_link = urlencode({'link': final_download_url})
        download_proxy_url = f'/download_proxy?{encoded_link}'

        # Frontende cavab göndərilir:
        return jsonify({
            "success": True,
            "download_url": download_proxy_url 
        })

    except Exception as e:
        app.logger.error(f"Video yükləmə zamanı xəta: {e}")
        return jsonify({"success": False, "message": f"Server tərəfdə gözlənilməz xəta: {str(e)}"}), 500


# --------------------------------------------------------------------------------
# ENDPOINT 2: /download_proxy (VİDEO FAYLINI DÜZGÜN HEADERLƏRLƏ ÖTÜRÜR)
# --------------------------------------------------------------------------------
@app.route('/download_proxy')
def download_proxy():
    # Linki query parametrindən alırıq
    final_url = request.args.get('link')

    if not final_url:
        return "Yükləmə linki tapılmadı.", 400

    try:
        response = requests.get(final_url, stream=True, timeout=30)
        response.raise_for_status() 

        # Fayl adı yaratmaq
        parsed_url = urlparse(final_url)
        filename = os.path.basename(parsed_url.path)
        
        if not filename or filename == 'video':
             filename = f"tiktok_video_{int(time.time())}.mp4"

        # ⚠️ ƏSAS HƏLL: Android DownloadManager-in tələb etdiyi düzgün headerlər
        headers = {
            "Content-Type": "video/mp4", 
            "Content-Disposition": f"attachment; filename=\"{filename}\"",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0" 
        }

        # Faylı birbaşa brauzerə ötürürük
        return Response(response.iter_content(chunk_size=8192), headers=headers)

    except requests.exceptions.HTTPError as e:
        return f"Yükləmə linki keçərsizdir və ya tapılmadı (HTTP Xətası: {e.response.status_code})", 404
    except Exception as e:
        return f"Proxylama zamanı gözlənilməz xəta: {str(e)}", 500


if __name__ == '__main__':
    # Canlı serverə yerləşdirəndə debug=False qoymağı unutmayın!
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8000), debug=True)