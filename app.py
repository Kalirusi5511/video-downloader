import os
import sys
import logging
import subprocess
import tempfile
import shutil
from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS

app = Flask(__name__)
# Erlaubt Anfragen von GitHub Pages
CORS(app, resources={r"/*": {"origins": "*"}})

# Einfaches Logging ohne extra-Felder (vermeidet KeyError)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)


@app.route('/')
def home():
    """Liefert die HTML-Oberfläche."""
    return render_template('index.html')


@app.route('/status')
def status():
    """Optionaler Health-Check als JSON."""
    return jsonify({"status": "Backend läuft einwandfrei"})


@app.route('/download', methods=['POST'])
def download():
    data = request.get_json() or {}
    video_url = data.get('url', '').strip()
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    if not video_url:
        return jsonify({'error': 'URL ist erforderlich'}), 400

    logger.info(f"Download angefordert von IP {client_ip} für URL: {video_url}")

    temp_dir = tempfile.mkdtemp()
    output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')

    try:
        # yt-dlp als Python-Modul aufrufen (zuverlässiger als Binary)
        cmd = [
            sys.executable, '-m', 'yt_dlp',
            '-f', 'b[ext=mp4]/best[ext=mp4]/best',
            '-o', output_template,
            '--no-playlist',
            video_url
        ]
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )

        downloaded_files = os.listdir(temp_dir)
        if not downloaded_files:
            return jsonify({'error': 'Keine Datei gefunden.'}), 500

        filepath = os.path.join(temp_dir, downloaded_files[0])
        logger.info(f"Download erfolgreich: {downloaded_files[0]}")

        return send_file(filepath, as_attachment=True)

    except subprocess.CalledProcessError as e:
        logger.error(f"yt-dlp Fehler: {e.stderr}")
        return jsonify({
            'error': 'Fehler beim Herunterladen von YouTube.',
            'details': e.stderr[-500:] if e.stderr else 'Unbekannt'
        }), 500
    except Exception as e:
        logger.error(f"Allgemeiner Fehler: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        # Temporären Ordner aufräumen (nach dem Senden)
        # Hinweis: send_file streamt die Datei; bei sehr großen Dateien
        # kann das Aufräumen zu früh kommen. Für kleinen Use-Case OK.
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
