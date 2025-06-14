from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from io import BytesIO

app = Flask(__name__)
recognizer = sr.Recognizer()

@app.route('/')
def index():
    return render_template('sttapi.html')

@app.route('/api/stream', methods=['POST'])
def stream_audio():
    # Nhận thẳng raw WAV bytes từ client
    audio_bytes = request.get_data()
    audio_file = BytesIO(audio_bytes)
    try:
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio, language='vi-VN')
        return jsonify({'status': 'success', 'text': text})
    except sr.UnknownValueError:
        return jsonify({'status': 'no-speech', 'text': ''})
    except sr.RequestError as e:
        return jsonify({'status': 'error', 'text': f'Lỗi request: {e}'})

if __name__ == '__main__':
    app.run(debug=True)
