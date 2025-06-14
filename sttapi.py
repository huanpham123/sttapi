import os
import numpy as np
import torch
import torchaudio
from flask import Flask, render_template, request, jsonify
from simple_websocket.ws import GeventWebSocket
from faster_whisper import WhisperModel

# --- Cấu hình ứng dụng và Mô hình ---
app = Flask(__name__)

# Chọn mô hình. "tiny", "base", "small", "medium".
# Bắt đầu với "base" để cân bằng tốc độ và độ chính xác.
# Nếu Vercel lỗi, hãy thử "tiny".
model_size = "base" 
# model_size = "vinai/vinai-whisper-base-vietnamese" # Nếu muốn dùng model tinh chỉnh

# Xác định thiết bị (CPU là lựa chọn an toàn cho Vercel)
device = "cuda" if torch.cuda.is_available() else "cpu"
compute_type = "float16" if device == "cuda" else "int8"

print(f"Đang tải mô hình Whisper ({model_size}) trên thiết bị {device}...")
# Tải mô hình một lần khi ứng dụng khởi động
# Vercel có thể tải lại ở mỗi request, đây là một điểm yếu
try:
    model = WhisperModel(model_size, device=device, compute_type=compute_type)
    print("Tải mô hình thành công.")
except Exception as e:
    print(f"Lỗi khi tải mô hình: {e}")
    model = None

# --- Route cho trang web ---
@app.route('/')
def index():
    """Phục vụ file HTML cho giao diện web."""
    return render_template('sttapi.html')

# --- API Endpoint cho Web (Streaming qua WebSocket) ---
@app.route('/stream')
def stream_socket(ws: GeventWebSocket):
    """Nhận audio stream từ trình duyệt, chuyển đổi và gửi lại văn bản."""
    if model is None:
        ws.send("Lỗi: Mô hình chưa được tải thành công.")
        return

    print("Client web đã kết nối WebSocket.")
    # Buffer để lưu các đoạn audio nhận được
    audio_buffer = bytearray()
    
    while not ws.closed:
        message = ws.receive()
        if message:
            # Dữ liệu nhận được là một chunk audio dạng blob
            audio_buffer.extend(message)
            
            # Chuyển đổi bytearray thành tensor audio
            # Dữ liệu từ trình duyệt thường là float32
            try:
                audio_np = np.frombuffer(audio_buffer, dtype=np.float32)
                # Whisper yêu cầu sample rate 16000
                # Cần resample nếu sample rate từ client khác (thường là 48000)
                # Tuy nhiên, để đơn giản, ta giả định client đã gửi đúng rate
                
                # Thực hiện nhận dạng
                segments, info = model.transcribe(audio_np, beam_size=5, language="vi")
                
                print(f"Ngôn ngữ được nhận diện: {info.language} với xác suất {info.language_probability}")
                
                full_text = "".join(segment.text for segment in segments)
                
                print(f"Đã nhận dạng: {full_text}")
                # Gửi kết quả (tạm thời) về cho client
                ws.send(full_text)
                
            except Exception as e:
                print(f"Lỗi xử lý audio: {e}")
                ws.send(f"[Lỗi: {e}]")

    print("Client web đã ngắt kết nối.")


# --- API Endpoint cho ESP32 (HTTP POST) ---
@app.route('/api/stt_esp32', methods=['POST'])
def stt_from_esp32():
    """
    Nhận dữ liệu audio (dạng thô, PCM 16-bit) từ ESP32 và trả về văn bản.
    """
    if model is None:
        return jsonify({"error": "Mô hình chưa được tải thành công."}), 500

    if not request.data:
        return jsonify({"error": "Không có dữ liệu audio"}), 400

    try:
        # Dữ liệu từ ESP32 là raw PCM 16-bit (int16)
        audio_bytes = request.data
        audio_np = np.frombuffer(audio_bytes, dtype=np.int16)

        # Chuyển đổi sang float32 và chuẩn hóa trong khoảng [-1, 1]
        audio_float32 = audio_np.astype(np.float32) / 32768.0
        
        # Thực hiện nhận dạng
        segments, info = model.transcribe(audio_float32, beam_size=5, language="vi")
        
        full_text = "".join(segment.text for segment in segments)
        print(f"ESP32 Transcript: {full_text}")
        
        return jsonify({"transcript": full_text})

    except Exception as e:
        print(f"Lỗi khi xử lý request từ ESP32: {e}")
        return jsonify({"error": str(e)}), 500

# Để chạy trên Vercel, dòng `if __name__ == '__main__':` không thực sự cần thiết
# Nhưng nó hữu ích để chạy thử trên máy local
if __name__ == '__main__':
    from gevent import pywsgi
    from geventwebsocket.handler import WebSocketHandler
    server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
    print("Server đang chạy tại http://localhost:5000")
    server.serve_forever()
