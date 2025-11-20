import os
import json
import yt_dlp
from flask import Flask, render_template, request, jsonify, make_response, send_from_directory

# Flask tətbiqinin yaradılması
app = Flask(__name__, template_folder='templates')

# ----------------------------------------------------------------------
# 1. ADS.TXT ROUTING (AdSense Təsdiqi Üçün)
# ----------------------------------------------------------------------

@app.route('/ads.txt')
def serve_ads_txt():
    """Google AdSense botları üçün ads.txt faylını təqdim edir."""
    # Kök qovluğu təyin edirik ki, faylı tapa bilək
    root_dir = os.path.dirname(os.path.abspath(__file__))
    return send_from_directory(root_dir, 'ads.txt')

# ----------------------------------------------------------------------
# 2. TEMPLATE ROUTING (Səhifələrin Naviqasiyası)
# ----------------------------------------------------------------------

@app.route('/')
def index():
    """Əsas yükləyici səhifəsini göstərir."""
    return render_template('index.html')

@app.route('/privacy')
def privacy_policy():
    """Məxfilik Siyasəti səhifəsini göstərir."""
    return render_template('privacy.html')

@app.route('/terms')
def terms_of_service():
    """İstifadə Şərtləri səhifəsini göstərir."""
    return render_template('terms.html')

@app.route('/blog')
def blog():
    """Blog səhifəsi."""
    return render_template('blog.html')

# ----------------------------------------------------------------------
# 3. YÜKLƏMƏ FUNKSİYASI (YENİLƏNMİŞ - yt-dlp ilə)
# ----------------------------------------------------------------------

@app.route('/api/download', methods=['POST'])
def download_video():
    """TikTok linkini emal edir və yükləmə linkini qaytarır (yt-dlp istifadə edərək)."""
    data = request.get_json()
    tiktok_url = data.get('url')

    if not tiktok_url or "tiktok.com" not in tiktok_url:
        return jsonify({'success': False, 'message': 'Zəhmət olmasa, düzgün bir TikTok URL-i daxil edin.'}), 400

    try:
        # yt-dlp konfiqurasiyası: Filigransız videonun URL-ni çəkmək üçün
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best', # Ən yaxşı MP4 formatını seçir
            'noplaylist': True,
            'skip_download': True,      # Yükləməyə ehtiyac yoxdur, sadəcə məlumatı çəkirik
            'quiet': True,              # Terminalda səs-küyü azaldır
            'simulate': True,           # Simulyasiya rejimi
            'force_generic_extractor': True, # Tik-Tok videoları üçün lazımdır
            'default_search': 'ytsearch', # Varsayılan axtarış rejimini düzəldir
            'extractor_args': ['tiktok:no_watermark'] # Mümkün qədər filigransız linki çəkməyə çalışır
        }

        # yt-dlp ilə metadata çəkirik
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # info_dict məlumatları çəkir
            info_dict = ydl.extract_info(tiktok_url, download=False)
            
            # Ən yaxşı yükləmə linkini tapırıq
            download_link = info_dict.get('url')
            video_title = info_dict.get('title', 'tiktok_video')
            
            # Alternativ olaraq, formatlar listindən link tapmağa çalışırıq
            if not download_link and info_dict.get('formats'):
                for f in info_dict['formats']:
                    if f.get('ext') == 'mp4' and f.get('url'):
                        download_link = f['url']
                        break

            if download_link:
                # Uğurla yükləmə linki tapıldı
                resp = make_response(jsonify({
                    'success': True, 
                    'download_url': download_link, 
                    'title': video_title.replace(' ', '_').replace('/', '') # Fayl adını təmizləyirik
                }))
                return resp, 200
            else:
                # Link tapılmadı
                print(f"yt-dlp yükləmə linkini tapa bilmədi: {json.dumps(info_dict)}")
                return jsonify({'success': False, 'message': 'Video yüklənmə linki tapılmadı.'}), 500

    except yt_dlp.utils.DownloadError as e:
        # yt-dlp xətaları, məsələn, video tapılmadı
        print(f"yt-dlp Xətası: {e}")
        return jsonify({'success': False, 'message': 'TikTok videosu tapılmadı və ya qapalıdır.'}), 500

    except Exception as e:
        # Digər gözlənilməz xətalar
        print(f"Gözlənilməz Xəta: {e}")
        return jsonify({'success': False, 'message': 'Gözlənilməz xəta baş verdi.'}), 500


if __name__ == '__main__':
    # PORT dəyişənini yoxlayır, yoxdusa 5000 istifadə edir
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)