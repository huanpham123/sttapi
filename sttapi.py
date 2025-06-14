import os
from flask import Flask, render_template, request, jsonify
from google.cloud import speech

app = Flask(__name__)

# --- Cấu hình cho Google Cloud ---
# !!! QUAN TRỌNG: Thay thế bằng API Key của bạn
# Để an toàn, hãy đặt nó trong biến môi trường trên Vercel
# GOOGLE_API_KEY = "YOUR_GOOGLE_CLOUD_API_KEY" 
# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'path/to/your/credentials.json' # Nếu dùng service account
# Thay vì set biến môi trường, chúng ta sẽ truyền API key trực tiếp (đơn giản hơn cho Vercel)

# --- Route cho trang web ---
@app.route('/')
def index():
    """Phục vụ file HTML cho giao diện web."""
    return render_template('sttapi.html')

# --- API Endpoint cho ESP32 ---
@app.route('/api/stt', methods=['POST'])
def stt_from_esp32():
    """
    Nhận dữ liệu audio (dạng thô, PCM) từ ESP32,
    gửi đến Google Speech-to-Text và trả về văn bản.
    """
    if not request.data:
        return jsonify({"error": "Không có dữ liệu audio"}), 400

    audio_content = request.data
    
    try:
        # Khởi tạo client cho mỗi yêu cầu để có thể truyền API key
        # Thay 'YOUR_GOOGLE_CLOUD_API_KEY' bằng key của bạn hoặc lấy từ biến môi trường
        api_key = os.environ.get('GOOGLE_API_KEY', None)
        client_options = {"api_key": api_key} if api_key else None
        
        client = speech.SpeechClient(client_options=client_options)

        audio = speech.RecognitionAudio(content=audio_content)
        
        # Cấu hình nhận dạng cho audio từ ESP32
        # INMP441 thường có sample rate là 16000Hz, định dạng PCM
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code="vi-VN"  # Ngôn ngữ Tiếng Việt
        )

        response = client.recognize(config=config, audio=audio)

        if not response.results:
            return jsonify({"transcript": ""})

        # Lấy kết quả có độ tin cậy cao nhất
        transcript = response.results[0].alternatives[0].transcript
        return jsonify({"transcript": transcript})

    except Exception as e:
        print(f"Lỗi khi gọi Google Speech API: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Chạy ở chế độ debug trên máy local
    app.run(debug=True, port=5000)
