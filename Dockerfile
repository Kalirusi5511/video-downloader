# Verwenden Sie das yt-dlp Image mit integriertem POT-Provider
# Dies behebt die "Sign in to confirm you're not a bot" Fehler
FROM ghcr.io/jim60105/yt-dlp:pot

# Arbeitsverzeichnis festlegen
WORKDIR /app

# Ihre Anwendung kopieren
COPY . .

# Abhängigkeiten installieren (Flask, CORS, etc.)
RUN pip install -r requirements.txt

# Startbefehl
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
