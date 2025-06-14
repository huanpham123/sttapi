import os
import json
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
from google.oauth2 import service_account
from google.cloud import speech

# --- Lấy credentials JSON từ biến môi trường và khởi tạo client ---
creds_info = os.environ.get("GOOGLE_CREDENTIALS_JSON")
if not creds_info:
    raise RuntimeError("Missing env var: GOOGLE_CREDENTIALS_JSON")
creds_dict = json.loads(creds_info)
credentials = service_account.Credentials.from_service_account_info(creds_dict)
client = speech.SpeechClient(credentials=credentials)

# --- Flask app setup ---
app = Flask(__name__, template_folder="templates")
CORS(app)

@app.route('/')
def index():
    return render_template('sttapi.html')

@app.route('/recognize', methods=['POST'])
def recognize():
    audio_bytes = request.data
    audio = speech.RecognitionAudio(content=audio_bytes)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="vi-VN",
        enable_automatic_punctuation=True,
    )
    response = client.recognize(config=config, audio=audio)
    texts = [res.alternatives[0].transcript for res in response.results]
    return jsonify({'transcript': ' '.join(texts)})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
