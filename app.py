from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import yt_dlp
import os
import threading

app = Flask(__name__)
CORS(app)

DOWNLOAD_FOLDER = 'downloads'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

tasks = {}

@app.route('/api/download', methods=['POST'])
def start_download():
    data = request.json
    url = data.get('url')
    task_id = str(len(tasks) + 1)
    
    def download():
        ydl_opts = {
            'outtmpl': f'{DOWNLOAD_FOLDER}/%(title)s.%(ext)s',
            'progress_hooks': [lambda d: update_progress(task_id, d)],
        }
        try:
            tasks[task_id]['status'] = 'downloading'
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                tasks[task_id]['status'] = 'completed'
                tasks[task_id]['filename'] = info.get('title', 'video') + '.' + info.get('ext', 'mp4')
        except Exception as e:
            tasks[task_id]['status'] = 'error'
            tasks[task_id]['error'] = str(e)
    
    tasks[task_id] = {'status': 'pending', 'progress': '0%', 'url': url, 'speed': '0'}
    threading.Thread(target=download, daemon=True).start()
    return jsonify({'task_id': task_id, 'task': tasks[task_id]})

def update_progress(task_id, d):
    if d['status'] == 'downloading':
        tasks[task_id]['progress'] = d.get('_percent_str', '0%')
        tasks[task_id]['speed'] = d.get('_speed_str', '0 B/s')
        tasks[task_id]['eta'] = d.get('_eta_str', '未知')

@app.route('/api/tasks/<task_id>')
def get_task(task_id):
    return jsonify(tasks.get(task_id, {}))

@app.route('/api/tasks')
def get_all_tasks():
    return jsonify(tasks)

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)