import os
import subprocess
import tempfile
from flask import Flask, request, send_file, jsonify
from flask_cors import CORS

app = Flask(__name__)
# Erlaubt Zugriff von GitHub Pages
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/')
def home():
    return jsonify({"status": "Backend running"})

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json() or {}
    video_url = data.get('url')

    if not video_url:
        return jsonify({'error': 'URL ist erforderlich'}), 400

    temp_dir = tempfile.mkdtemp()
    output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')

    try:
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
            return jsonify({'error': 'Video konnte nicht abgerufen werden.'}), 500

        filepath = os.path.join(temp_dir, downloaded_files[0])
        return send_file(filepath, as_attachment=True)

    except subprocess.CalledProcessError:
        return jsonify({'error': 'Fehler beim Verarbeiten des Links.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
