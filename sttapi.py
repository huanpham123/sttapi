from flask import Flask, render_template, request, jsonify, Response
import speech_recognition as sr
from io import BytesIO
import threading
from queue import Queue
import time

app = Flask(__name__)
recognizer = sr.Recognizer()
audio_queue = Queue()
result_queue = Queue()
stop_event = threading.Event()

def process_audio():
    while not stop_event.is_set():
        if not audio_queue.empty():
            audio_data = audio_queue.get()
            
            try:
                # Convert bytes to AudioData
                audio_file = BytesIO(audio_data)
                with sr.AudioFile(audio_file) as source:
                    audio = recognizer.record(source)
                
                text = recognizer.recognize_google(audio, language='vi-VN')  # Change language as needed
                result_queue.put({'text': text, 'status': 'success'})
            except sr.UnknownValueError:
                result_queue.put({'text': "", 'status': 'no-speech'})
            except sr.RequestError as e:
                result_queue.put({'text': f"Error: {str(e)}", 'status': 'error'})
        else:
            time.sleep(0.1)

# Start processing thread
processing_thread = threading.Thread(target=process_audio)
processing_thread.daemon = True
processing_thread.start()

@app.route('/')
def index():
    return render_template('sttapi.html')

@app.route('/api/stream', methods=['POST'])
def stream_audio():
    audio_data = request.data
    audio_queue.put(audio_data)
    
    # Wait for result with timeout
    try:
        result = result_queue.get(timeout=5)
        return jsonify(result)
    except:
        return jsonify({'text': '', 'status': 'timeout'})

@app.route('/api/stream_events', methods=['POST'])
def stream_events():
    def generate():
        while True:
            audio_data = request.stream.read(1024)
            if not audio_data:
                break
            
            audio_queue.put(audio_data)
            
            if not result_queue.empty():
                result = result_queue.get()
                yield f"data: {json.dumps(result)}\n\n"
    
    return Response(generate(), mimetype='text/event-stream')

def cleanup():
    stop_event.set()
    processing_thread.join()

if __name__ == '__main__':
    try:
        app.run(debug=True)
    finally:
        cleanup()
