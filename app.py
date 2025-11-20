import os
import json
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory

# Logging səviyyəsini tənzimləyir
logging.basicConfig(level=logging.INFO)

# app.py faylının yerləşdiyi qovluğun yolu
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Flask tətbiqini inisializasiya edir
app = Flask(__name__, template_folder='templates')

# Yükləmələrin saxlanılacağı qovluğu təyin et
DOWNLOAD_FOLDER = 'downloads'
# Bu qovluq BASE_DIR içində olmalıdır
DOWNLOAD_PATH = os.path.join(BASE_DIR, DOWNLOAD_FOLDER)
if not os.path.exists(DOWNLOAD_PATH):
    os.makedirs(DOWNLOAD_PATH)

# ------------------------------------
# 1. TEMPLATE ROUTING (HTML SƏHİFƏLƏRİ)
# ------------------------------------

@app.route('/')
def index():
    """Əsas səhifəni yükləyir."""
    return render_template('index.html')

@app.route('/blog.html')
def blog():
    """Bloq səhifəsini yükləyir."""
    return render_template('blog.html')

@app.route('/privacy.html')
def privacy():
    """Gizlilik siyasəti səhifəsini yükləyir."""
    return render_template('privacy.html')

@app.route('/terms.html')
def terms():
    """İstifadə şərtləri səhifəsini yükləyir."""
    return render_template('terms.html')

# ------------------------------------
# 2. ADS.TXT ROUTING (ADS.TXT FAYLI)
# ------------------------------------

@app.route('/ads.txt')
def serve_ads_txt():
    """
    Google AdSense ads.txt faylını tətbiqin əsas qovluğundan təqdim edir.
    """
    # os.getcwd() əvəzinə BASE_DIR istifadə edərək faylın yerini daha dəqiq təyin edirik.
    try:
        # Faylın adı: 'ads.txt'
        # Faylın yerləşdiyi qovluq: BASE_DIR (app.py-nin yerləşdiyi yer)
        return send_from_directory(BASE_DIR, 'ads.txt')
    except Exception as e:
        app.logger.error(f"Error serving ads.txt: {e}")
        # Fayl tapılmasa, xəta qaytarılır
        return "Not Found", 404


# ------------------------------------
# 3. DOWNLOAD LOGIC (YÜKLƏMƏ MƏNTİQİ)
# ------------------------------------

@app.route('/yukle', methods=['POST'])
def yukle():
    """
    TikTok linkini alır, videonu yükləyir və yükləmə linkini geri qaytarır.
    (Məntiq demo kimi saxlanılır.)
    """
    try:
        data = request.get_json()
        video_url = data.get('url')

        if not video_url or 'tiktok.com' not in video_url:
            return jsonify({'success': False, 'message': 'Keçərli TikTok URL-i daxil edin.'})
        
        # Real yükləmə prosesi (yt-dlp ilə) bu hissədə olmalıdır.

        # Nümunə yükləmə URL-i (Real tətbiqdə bu dinamik olmalıdır)
        download_link = "/downloads/test_video.mp4" 

        return jsonify({
            'success': True, 
            'message': 'Yükləmə uğurla tamamlandı. Link hazırlanır.', 
            'download_url': download_link 
        })

    except Exception as e:
        app.logger.error(f"Yükləmə xətası: {e}")
        return jsonify({'success': False, 'message': f'Server xətası: {e}'})

if __name__ == '__main__':
    # Flask tətbiqini işə salır.
    app.run(debug=True, host='0.0.0.0', port=5000)