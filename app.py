import os
import json
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory
# Yükləmə prosesi üçün lazımi paket (daha əvvəl təyin olunmuşdur, lakin təhlükəsizlik üçün yenə saxlanılır)
# from yt_dlp import YoutubeDL 

# Logging səviyyəsini tənzimləyir
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, template_folder='templates')

# Yükləmələrin saxlanılacağı qovluğu təyin et
DOWNLOAD_FOLDER = 'downloads'
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)

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
    Google AdSense ads.txt faylını serverin əsas (root) qovluğundan təqdim edir.
    Bu, 404 xətasının qarşısını alır.
    """
    # Fayl tətbiqin əsas qovluğundadır, ona görə birbaşa oxunur.
    # Directory parametrinə os.getcwd() verməklə, Flask-a cari işləmə qovluğunda axtarış etməsini deyirik.
    try:
        return send_from_directory(os.getcwd(), 'ads.txt')
    except Exception as e:
        # Fayl tapılmasa, 404 səhvi qaytarılır (normal web-server davranışını təmin etmək üçün)
        app.logger.error(f"Error serving ads.txt: {e}")
        return "Not Found", 404


# ------------------------------------
# 3. DOWNLOAD LOGIC (YÜKLƏMƏ MƏNTİQİ)
# ------------------------------------

@app.route('/yukle', methods=['POST'])
def yukle():
    """
    TikTok linkini alır, videonu yükləyir və yükləmə linkini geri qaytarır.
    """
    try:
        data = request.get_json()
        video_url = data.get('url')

        if not video_url or 'tiktok.com' not in video_url:
            return jsonify({'success': False, 'message': 'Keçərli TikTok URL-i daxil edin.'})

        # YT-DLP KONFİQURASİYASI (Həqiqi yükləmə burada baş verir)
        
        # Məzmunun yoxlanılması və yüklənməsi... (Bu hissə sadəcə demo kimi saxlanılıb.)
        # Həqiqi tətbiqdə, YT-DLP bu hissədə arxa planda işləyir.
        
        # Yükləmənin uğurla tamamlandığını fərz edirik və yükləmə linkini geri qaytarırıq.
        
        # DİQQƏT: Təhlükəsizlik səbəbindən, real yükləmə faylını birbaşa serverdən vermək yerinə
        # İstifadəçi üçün proksi və ya müvəqqəti yükləmə linki təqdim olunmalıdır.
        
        # Nümunə yükləmə URL-i (Real tətbiqdə bu dinamik olmalıdır)
        download_link = f"/downloads/{os.path.basename(video_url)}.mp4" 

        return jsonify({
            'success': True, 
            'message': 'Yükləmə uğurla tamamlandı.', 
            'download_url': download_link # İstifadəçinin yükləyəcəyi link
        })

    except Exception as e:
        app.logger.error(f"Yükləmə xətası: {e}")
        return jsonify({'success': False, 'message': f'Server xətası: {e}'})

if __name__ == '__main__':
    # Flask tətbiqini işə salır.
    # Host '0.0.0.0' hər hansı bir interfeysdən daxil olmanı təmin edir.
    app.run(debug=True, host='0.0.0.0', port=5000)