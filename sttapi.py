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
    try:
        audio_data = request.data
        audio_file = BytesIO(audio_data)
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio, language='vi-VN')
        return jsonify({'text': text, 'status': 'success'})
    except sr.UnknownValueError:
        return jsonify({'text': '', 'status': 'no-speech'})
    except sr.RequestError as e:
        return jsonify({'text': f"Lỗi: {str(e)}", 'status': 'error'})

if __name__ == '__main__':
    app.run(debug=True)
