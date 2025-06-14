from flask import Flask, render_template, request, jsonify
import speech_recognition as sr
from io import BytesIO
import threading

app = Flask(__name__)
recognizer = sr.Recognizer()
audio_queue = []
processing = False

@app.route('/')
def index():
    return render_template('sttapi.html')

@app.route('/api/stream', methods=['POST'])
def stream_audio():
    global processing
    
    if not processing:
        processing = True
        audio_data = request.data
        
        try:
            # Convert bytes to AudioData
            audio_file = BytesIO(audio_data)
            with sr.AudioFile(audio_file) as source:
                audio = recognizer.record(source)
            
            text = recognizer.recognize_google(audio, language='vi-VN')  # Change language as needed
            return jsonify({'text': text, 'status': 'success'})
        except sr.UnknownValueError:
            return jsonify({'text': "Could not understand audio", 'status': 'error'})
        except sr.RequestError as e:
            return jsonify({'text': f"Error: {str(e)}", 'status': 'error'})
        finally:
            processing = False
    else:
        return jsonify({'text': "Processing previous request", 'status': 'busy'})

if __name__ == '__main__':
    app.run(debug=True)
