import os
import io
from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
from google.cloud import speech

# Khởi tạo Flask
app = Flask(__name__)
CORS(app)

# Khởi tạo client của Google Speech-to-Text
# Bạn cần set biến môi trường GOOGLE_APPLICATION_CREDENTIALS
client = speech.SpeechClient()

@app.route('/')
def index():
    return render_template('sttapi.html')

@app.route('/recognize', methods=['POST'])
def recognize():
    """
    Nhận một blob audio WAV (Linear16, 16kHz, mono) và trả về transcript.
    """
    audio_bytes = request.data
    audio = speech.RecognitionAudio(content=audio_bytes)

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code="vi-VN",
        enable_automatic_punctuation=True,
    )

    # Gửi request sync
    response = client.recognize(config=config, audio=audio)

    # Ghép tất cả kết quả
    texts = [result.alternatives[0].transcript for result in response.results]
    return jsonify({'transcript': ' '.join(texts)})

if __name__ == '__main__':
    # Port do Vercel truyền vào qua env var PORT
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
