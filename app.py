import os
import shutil
import random
import socket
import time
import threading # NEW IMPORT
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from flask_socketio import SocketIO, emit, join_room
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'fallback_key_for_dev_only')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024 # 100 MB Limit

limiter = Limiter(get_remote_address, app=app, storage_uri="memory://")
socketio = SocketIO(app)

# active_rooms now stores: {"clipboard": "...", "last_active": 1690000000.0}
active_rooms = {}

UPLOAD_FOLDER = 'uploads'
if os.path.exists(UPLOAD_FOLDER):
    shutil.rmtree(UPLOAD_FOLDER)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_room_folder(room_code):
    folder = os.path.join(app.config['UPLOAD_FOLDER'], str(room_code))
    os.makedirs(folder, exist_ok=True)
    return folder

# --- DOS MITIGATION: AUTOMATED CLEANUP THREAD ---
def cleanup_inactive_rooms():
    while True:
        time.sleep(600) # Wait 10 minutes between checks
        current_time = time.time()
        rooms_to_delete = []
        
        # Find rooms inactive for more than 1 hour (3600 seconds)
        for room_code, data in active_rooms.items():
            if current_time - data['last_active'] > 3600:
                rooms_to_delete.append(room_code)
                
        # Delete the abandoned rooms
        for room_code in rooms_to_delete:
            print(f"Server Cleanup: Deleting inactive room {room_code}")
            del active_rooms[room_code]
            room_folder = get_room_folder(room_code)
            if os.path.exists(room_folder):
                shutil.rmtree(room_folder)

# Start the background thread immediately
cleanup_thread = threading.Thread(target=cleanup_inactive_rooms, daemon=True)
cleanup_thread.start()

# Helper to refresh the timer whenever someone does something in a room
def refresh_room_timer(room_code):
    if room_code in active_rooms:
        active_rooms[room_code]['last_active'] = time.time()

# --- ERROR HANDLERS ---
@app.errorhandler(413)
def file_too_large(e):
    return jsonify({"status": "error", "message": "File exceeds the 100MB limit!"}), 413

@app.errorhandler(429)
def ratelimit_exceeded(e):
    return jsonify({"status": "error", "message": "Slow down! Maximum 30 files per minute."}), 429

# --- WEB INTERFACE ---
@app.route('/', methods=['GET'])
def home():
    room_code = session.get('room_code')
    if room_code and room_code in active_rooms:
        refresh_room_timer(room_code)
        return render_template('index.html', logged_in=True, room_code=room_code)
    return render_template('index.html', logged_in=False, error=request.args.get('error'))

@app.route('/create_room', methods=['POST'])
def create_room():
    if len(active_rooms) >= 10:
        return redirect(url_for('home', error="Server is full! Maximum of 10 active rooms reached. Please try again later."))

    room_code = str(random.randint(1000, 9999))
    while room_code in active_rooms: 
        room_code = str(random.randint(1000, 9999))
        
    active_rooms[room_code] = {
        "clipboard": "Welcome to your private room!",
        "last_active": time.time() # Start the clock!
    }
    session['room_code'] = room_code
    return redirect(url_for('home'))

@app.route('/join_room', methods=['POST'])
def join_room_route():
    entered_code = request.form.get('room_code')
    if entered_code in active_rooms:
        session['room_code'] = entered_code
        refresh_room_timer(entered_code)
        return redirect(url_for('home'))
    else:
        return redirect(url_for('home', error="Room not found or has expired. Check the code and try again."))

@app.route('/leave_room')
def leave_room_route():
    session.pop('room_code', None)
    return redirect(url_for('home'))

# --- WEBSOCKETS ---
@socketio.on('join')
def on_join():
    room = session.get('room_code')
    if room and room in active_rooms:
        join_room(room)
        refresh_room_timer(room)

@socketio.on('text_update')
def handle_text_update(data):
    room = session.get('room_code')
    if room and room in active_rooms:
        active_rooms[room]['clipboard'] = data['text']
        refresh_room_timer(room) # Reset the clock when they type
        emit('text_received', {'text': data['text']}, to=room, include_self=False)

# --- API ROUTES ---
# --- PWA ROUTES ---
@app.route('/manifest.json')
def serve_manifest():
    return send_from_directory('static', 'manifest.json')

@app.route('/sw.js')
def serve_sw():
    return send_from_directory('static', 'sw.js', mimetype='application/javascript')
@app.route('/api/clipboard', methods=['GET'])
def get_initial_clipboard():
    room = session.get('room_code')
    if not room or room not in active_rooms:
        return jsonify({"status": "error"}), 401
    refresh_room_timer(room)
    return jsonify({"text": active_rooms[room]['clipboard']})

@app.route('/api/upload', methods=['POST'])
@limiter.limit("30 per minute")
def upload_file():
    room = session.get('room_code')
    if not room or room not in active_rooms:
        return jsonify({"status": "error"}), 401
        
    if 'file' not in request.files:
        return jsonify({"status": "error"}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error"}), 400
    
    filename = secure_filename(file.filename)
    room_folder = get_room_folder(room)
    file.save(os.path.join(room_folder, filename))
    
    refresh_room_timer(room) # Reset the clock when they upload
    socketio.emit('file_uploaded', to=room)
    return jsonify({"status": "success"})

@app.route('/api/files', methods=['GET'])
def list_files():
    room = session.get('room_code')
    if not room or room not in active_rooms:
        return jsonify({"status": "error"}), 401
        
    room_folder = get_room_folder(room)
    files = os.listdir(room_folder) if os.path.exists(room_folder) else []
    refresh_room_timer(room)
    return jsonify({"files": files})

@app.route('/download/<filename>')
def download_file(filename):
    room = session.get('room_code')
    if not room or room not in active_rooms:
        return jsonify({"status": "error"}), 401
    room_folder = get_room_folder(room)
    refresh_room_timer(room)
    return send_from_directory(room_folder, filename, as_attachment=True)

@app.route('/api/clear', methods=['POST'])
def clear_data():
    room = session.get('room_code')
    if not room or room not in active_rooms:
        return jsonify({"status": "error"}), 401
    
    active_rooms[room]['clipboard'] = ""
    room_folder = get_room_folder(room)
    if os.path.exists(room_folder):
        shutil.rmtree(room_folder)
    os.makedirs(room_folder, exist_ok=True)
    
    refresh_room_timer(room)
    socketio.emit('text_received', {'text': ''}, to=room)
    socketio.emit('file_uploaded', to=room)
    return jsonify({"status": "success"})

if __name__ == '__main__':
    hostname = socket.gethostname()
    print("\n" + "="*50)
    print(f"📱 Local Testing URL:")
    print(f"👉 http://{hostname}.local:5000 👈")
    print("="*50 + "\n")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)