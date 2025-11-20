import os
import requests
from flask import Flask, render_template, request, jsonify, make_response, send_from_directory

# Flask tətbiqinin yaradılması və şablon qovluğunun təyin edilməsi
app = Flask(__name__, template_folder='templates')

# TikTok API-si üçün müvəqqəti URL (funksionallıq üçün placeholder)
TIKTOK_DOWNLOAD_API = "https://example-tiktok-api.com/download"

# ----------------------------------------------------------------------
# 1. ADS.TXT ROUTING (AdSense Təsdiqi Üçün Mütləqdir)
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

@app.route('/blog') # ❗ YENİ BLOG MARŞRUTU ƏLAVƏ EDİLDİ ❗
def blog():
    """AdSense tələbləri üçün əlavə dəyərli məzmun təqdim edən blog səhifəsi."""
    return render_template('blog.html')

# ----------------------------------------------------------------------
# 3. YÜKLƏMƏ FUNKSİYASI (MÖVCUD)
# ----------------------------------------------------------------------

@app.route('/api/download', methods=['POST'])
def download_video():
    """TikTok linkini emal edir və yükləmə linkini qaytarır."""
    data = request.get_json()
    tiktok_url = data.get('url')

    if not tiktok_url:
        return jsonify({'success': False, 'message': 'Zəhmət olmasa, düzgün bir TikTok URL-i daxil edin.'}), 400

    try:
        # Xarici API-yə müraciət (nümunə üçün)
        response = requests.post(TIKTOK_DOWNLOAD_API, json={'url': tiktok_url})
        response.raise_for_status() # HTTP xətaları üçün

        api_data = response.json()

        if api_data.get('success'):
            # Müvəffəqiyyətli API cavabı
            download_link = api_data.get('download_url')
            video_title = api_data.get('title', 'tiktok_video')
            
            # Faylı brauzerə göndərmək üçün cavab hazırlayırıq
            resp = make_response(jsonify({'success': True, 'download_url': download_link, 'title': video_title}))
            return resp

        else:
            # API-dən gələn uğursuz cavab
            return jsonify({'success': False, 'message': api_data.get('message', 'Video yüklənmədi. Linki yoxlayın.')}), 500

    except requests.exceptions.RequestException as e:
        # API müraciətindəki xətaları idarə et
        print(f"API Müraciət Xətası: {e}")
        return jsonify({'success': False, 'message': 'Server xətası: Yükləmə xidməti hazırda əlçatan deyil.'}), 500

    except Exception as e:
        # Digər gözlənilməz xətalar
        print(f"Gözlənilməz Xəta: {e}")
        return jsonify({'success': False, 'message': 'Gözlənilməz xəta baş verdi.'}), 500


if __name__ == '__main__':
    # PORT dəyişənini yoxlayır, yoxdusa 5000 istifadə edir
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)