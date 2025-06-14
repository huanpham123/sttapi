from flask import Flask, render_template, request, jsonify
from io import BytesIO
import speech_recognition as sr
import threading
import time

app = Flask(__name__)
recognizer = sr.Recognizer()

# Thread-safe queue for audio processing
audio_queue = []
processing_lock = threading.Lock()
stop_processing = False

def audio_processor():
    global stop_processing
    while not stop_processing:
        with processing_lock:
            if audio_queue:
                audio_data = audio_queue.pop(0)
            else:
                audio_data = None
        
        if audio_data:
            try:
                # Convert bytes to AudioData
                audio_file = BytesIO(audio_data)
                with sr.AudioFile(audio_file) as source:
                    audio = recognizer.record(source)
                
                # Recognize speech
                text = recognizer.recognize_google(audio, language='vi-VN')
                audio_data['result'] = text
                audio_data['status'] = 'success'
            except sr.UnknownValueError:
                audio_data['status'] = 'no-speech'
                audio_data['result'] = ""
            except sr.RequestError as e:
                audio_data['status'] = 'error'
                audio_data['result'] = f"Error: {str(e)}"
            except Exception as e:
                audio_data['status'] = 'error'
                audio_data['result'] = f"Unexpected error: {str(e)}"
        
        time.sleep(0.1)

# Start processing thread
processing_thread = threading.Thread(target=audio_processor)
processing_thread.daemon = True
processing_thread.start()

@app.route('/')
def index():
    return render_template('sttapi.html')

@app.route('/api/stream', methods=['POST'])
def stream_audio():
    audio_data = request.data
    request_id = str(time.time())  # Unique ID for this request
    
    # Create an entry in the queue
    queue_entry = {
        'id': request_id,
        'data': audio_data,
        'status': 'processing',
        'result': None
    }
    
    with processing_lock:
        audio_queue.append(queue_entry)
    
    # Wait for processing to complete (with timeout)
    start_time = time.time()
    while time.time() - start_time < 5:  # 5-second timeout
        with processing_lock:
            if queue_entry['status'] != 'processing':
                break
        time.sleep(0.1)
    
    if queue_entry['status'] == 'processing':
        return jsonify({'text': '', 'status': 'timeout'})
    
    return jsonify({
        'text': queue_entry['result'],
        'status': queue_entry['status']
    })

def cleanup():
    global stop_processing
    stop_processing = True
    processing_thread.join()

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        cleanup()
