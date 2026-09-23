import os
import subprocess
import tempfile
from flask import Flask, render_template_string, request, send_file, jsonify

app = Flask(__name__)

# Simple, responsive frontend HTML UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Educational Video Downloader</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
        body { background: #f4f6f8; display: flex; align-items: center; justify-content: center; min-height: 100vh; padding: 20px; }
        .card { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); width: 100%; max-width: 480px; }
        h1 { font-size: 1.5rem; color: #1a1a1a; margin-bottom: 8px; }
        p { color: #666; font-size: 0.9rem; margin-bottom: 20px; }
        input[type="text"] { width: 100%; padding: 12px 16px; border: 1px solid #ccc; border-radius: 8px; font-size: 0.95rem; margin-bottom: 16px; outline: none; }
        input[type="text"]:focus { border-color: #2563eb; }
        button { width: 100%; padding: 12px; background: #2563eb; color: white; border: none; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: background 0.2s; }
        button:hover { background: #1d4ed8; }
        #status { margin-top: 16px; font-size: 0.9rem; text-align: center; color: #4b5563; }
    </style>
</head>
<body>
    <div class="card">
        <h1>Video Downloader</h1>
        <p>Paste an open/educational video URL to download.</p>
        <form id="downloadForm">
            <input type="text" id="url" placeholder="https://..." required />
            <button type="submit" id="btn">Download Video</button>
        </form>
        <div id="status"></div>
    </div>

    <script>
        document.getElementById('downloadForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const urlInput = document.getElementById('url').value;
            const status = document.getElementById('status');
            const btn = document.getElementById('btn');

            status.textContent = "Processing and downloading video... Please wait.";
            btn.disabled = true;

            try {
                const response = await fetch('/download', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: urlInput })
                });

                if (!response.ok) {
                    const err = await response.json();
                    throw new Error(err.error || 'Failed to download.');
                }

                // Trigger direct file download in browser
                const blob = await response.blob();
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = downloadUrl;
                
                // Get filename from header or fallback
                const contentDisposition = response.headers.get('Content-Disposition');
                let filename = 'video.mp4';
                if (contentDisposition) {
                    const match = contentDisposition.match(/filename="?([^"]+)"?/);
                    if (match && match[1]) filename = match[1];
                }
                
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                a.remove();
                status.textContent = "Download complete!";
            } catch (err) {
                status.textContent = "Error: " + err.message;
            } finally {
                btn.disabled = false;
            }
        });
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    video_url = data.get('url')

    if not video_url:
        return jsonify({'error': 'URL is required'}), 400

    temp_dir = tempfile.mkdtemp()
    output_template = os.path.join(temp_dir, '%(title)s.%(ext)s')

    try:
        # Run yt-dlp binary to fetch MP4 video stream
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
            return jsonify({'error': 'Could not retrieve video file.'}), 500

        filepath = os.path.join(temp_dir, downloaded_files[0])
        return send_file(filepath, as_attachment=True)

    except subprocess.CalledProcessError:
        return jsonify({'error': 'Failed to process video link.'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
