import os
import time
import requests
import yt_dlp # Modulun düzgün idxalı: tire (-) əvəzinə alt xətt (_) istifadə olunur
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename

# Flask tətbiqinin yaradılması
# 'templates' qovluğu Render-də HTML fayllarını tapmaq üçün vacibdir
app = Flask(__name__, template_folder='templates')

# Qovluq konfiqurasiyası
# Render fayl sistemi müvəqqəti olduğundan bu qovluq lokal testlər üçün nəzərdə tutulub
UPLOAD_FOLDER = 'downloads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# --- Routing ---

# Əsas səhifə (index.html)
@app.route('/')
def index():
    return render_template('index.html')

# Məxfilik Siyasəti səhifəsi
@app.route('/privacy')
def privacy():
    # Bu faylın mövcudluğunu yoxlayın
    return render_template('privacy.html') 

# İstifadə Şərtləri səhifəsi
@app.route('/terms')
def terms():
    # Bu faylın mövcudluğunu yoxlayın
    return render_template('terms.html') 

# Bloq səhifəsi - sadə placeholder (əgər yaradılıbsa)
@app.route('/blog')
def blog():
    # Bu faylın mövcudluğunu yoxlayın
    return render_template('blog.html')

# --- API Endpoints ---

@app.route('/api/download', methods=['POST'])
def download_video():
    """
    TikTok linkini qəbul edir və yt-dlp vasitəsilə
    filiqransız yükləmə linkini qaytarır.
    """
    try:
        data = request.get_json()
        url = data.get('url')

        if not url:
            return jsonify({'success': False, 'message': 'Zəhmət olmasa, etibarlı bir link daxil edin.'}), 400

        # Yükləmənin deyil, sadəcə məlumatların əldə edilməsi üçün yt-dlp konfiqurasiyası
        ydl_opts = {
            # Həqiqi yükləmə əvəzinə məlumatları çıxarmaq
            'simulate': True, 
            # Yükləmə prosesini tərk etmək
            'skip_download': True,
            # Xəbərdarlıqları gizlətmək
            'no_warnings': True,
            # Konsol çıxışını səssiz etmək
            'quiet': True,
            # Ən yaxşı, filiqransız axını seçməyə imkan verən xüsusi TikTok extractor-u işə salır
            'force_generic_extractor': False,
        }
        
        # yt-dlp ilə məlumatları əldə et
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # yt-dlp ən yaxşı video/audio axınını (adətən filiqransız olanı) tapır
            info_dict = ydl.extract_info(url, download=False)
            
            # Əgər bu bir playlistdirsə, sadəcə ilk elementi götürürük
            video_info = info_dict['entries'][0] if 'entries' in info_dict and info_dict['entries'] else info_dict
            
            # Yükləmə linkini və başlıq tapmaq
            final_url = None
            title = video_info.get('title', 'tiktok_video')

            # Ən keyfiyyətli MP4 axınını tapın
            if 'formats' in video_info:
                for f in video_info['formats']:
                    # MP4 formatını və HTTPS protokolunu axtarırıq
                    if f.get('ext') == 'mp4' and f.get('protocol') in ['https', 'http']:
                        final_url = f['url']
                        break
            
            if final_url:
                return jsonify({
                    'success': True,
                    # Təhlükəsiz fayl adı yaratmaq
                    'title': secure_filename(title).replace('_', ' ').strip(), 
                    'download_url': final_url 
                })
            else:
                return jsonify({'success': False, 'message': 'Uyğun MP4 axını tapılmadı. Video silinmiş ola bilər və ya gizlidir.'}), 404

    except yt_dlp.utils.DownloadError as e:
        # yt-dlp xətalarını qeyd et
        app.logger.error(f"yt-dlp Download Error: {e}")
        return jsonify({'success': False, 'message': 'TikTok linkini emal edərkən xəta baş verdi. Zəhmət olmasa, linkin düzgün olduğundan əmin olun.'}), 500
        
    except Exception as e:
        # Digər gözlənilməz xətalar
        app.logger.error(f"Gözlənilməz Xəta: {e}")
        return jsonify({'success': False, 'message': 'Gözlənilməz server xətası baş verdi. Yenidən cəhd edin.'}), 500


if __name__ == '__main__':
    # Local inkişaf mühiti üçün. Render Procfile-dan istifadə edəcək.
    app.run(debug=True, host='0.0.0.0', port=5000)