import os
import logging
import subprocess
import tempfile
from datetime import datetime
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Erlaubt Anfragen von GitHub Pages
CORS(app, resources={r"/*": {"origins": "*"}})

# Log-Einstellungen für das Render-Dashboard und lokale Dateien
LOG_FILE = 'downloads.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] IP: %(client_ip)s - URL: %(video_url)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()  # Zeigt die Logs direkt im Render-Terminal an
    ]
)

@app.route('/')
def home():
    return jsonify({"status": "Backend läuft einwandfrei"})

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json() or {}
    video_url = data.get('url', '').strip()
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    if not video_url:
        return jsonify({'error': 'URL ist erforderlich'}), 400

    # Protokolliere den Versuch in den Logs
    extra = {'client_ip': client_ip, 'video_url': video_url}
    logging.info("Download angefordert", extra=extra)

    temp_dir = tempfile.mkdtemp()
    output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')

    try:
        # yt-dlp lädt das MP4-Video herunter
        cmd = [
            'yt-dlp',
            '-f', 'b[ext=mp4]/best[ext=mp4]/best',
            '-o', output_template,
            '--no-playlist',
            video_url
        ]
        subprocess.run(cmd, check=True)

        downloaded_files = os.listdir(temp_dir)
        if not downloaded_files:
            return jsonify({'error': 'Keine Datei gefunden.'}), 500

        filepath = os.path.join(temp_dir, downloaded_files[0])
        return send_file(filepath, as_attachment=True)

    except subprocess.CalledProcessError:
        logging.error(f"Fehler bei yt-dlp für URL: {video_url}", extra={'client_ip': client_ip, 'video_url': video_url})
        return jsonify({'error': 'Fehler beim Herunterladen von YouTube.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
