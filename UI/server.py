from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import os
import sys
import random
from flask_cors import CORS
from pydantic import BaseModel
import logging
from multiprocessing import Process, Value, Queue

gesture_queue = Queue()
eye_queue = Queue()
head_queue = Queue()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from Audio.main import audio_recognition, audio_start
from FusionGesture.main import fusion_gesture_start
from Database.user import UserManager

app = Flask(__name__)
CORS(app)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

admins = {"alice", "bob"}
users = {"carol", "dave", "eve"}

class LoginRequest(BaseModel):
    username: str

@app.post("/login")
def login():
    data = request.get_json()  
    if not data or "username" not in data:
        return jsonify(success=False, message="缺少用户名"), 400

    username = data["username"].strip()
    print(f"登录用户: {username}")

    if username in admins:
        user = user_manager.authenticate(username, is_admin=True)
        return jsonify(success=True, is_admin=True)
    elif username in users:
        user = user_manager.authenticate(username, is_admin=False)
        return jsonify(success=True, is_admin=False)
    else:
        return jsonify(success=False, message="用户不存在")
    
gesture_number = 0
voice_number = 0
head_number = 0
eye_number = 0

def translate_gesture(label):
    if label == 'fist':
        return 7
    elif label == 'palm':
        return 4
    else:
        return 0

def translate_eye(label):
    if label == 'CENTER':
        return 5
    else:
        return 2
    
def translate_head(label):
    if label == 'NOD':
        return 3
    elif label == 'SHAKE':
        return 6
    else:
        return 0

@app.route('/gesture-result')
def gesture_result():
    global gesture_number
    try:
        current_label = gesture_queue.get_nowait()  # 非阻塞读取
        print(f"当前手势: {current_label}")
    except:
        current_label = ""
    gesture_number = translate_gesture(current_label) 
    return jsonify(code=gesture_number)

@app.route('/voice-result')
def voice_result():
    global voice_number
    return jsonify(code=voice_number)

@app.route('/head-result')
def head_result():
    global head_number
    try:
        current_label = head_queue.get_nowait()  # 非阻塞读取
        print(f"当前头部动作: {current_label}")
    except:
        current_label = ""
    head_number = translate_head(current_label)
    return jsonify(code=head_number)

@app.route('/eye-result')
def eye_result():
    global eye_number
    try:
        current_label = eye_queue.get_nowait()  # 非阻塞读取
        print(f"当前眼部动作: {current_label}")
    except:
        current_label = ""
    eye_number = translate_eye(current_label)
    return jsonify(code=eye_number)

@app.route('/start-record', methods=['POST'])
def start_record():
    data = request.get_json()
    if data.get("flag") == True:
        print("开始录音...")
        global voice_number
        
        result = audio_recognition()
        print("录音结束，结果:", result)
        voice_number = result
        return jsonify(success=True)
    else:
        return jsonify(success=False), 400

if __name__ == '__main__':
    print("---Starting audio device...")
    audio_start() 
    print("---Audio device started successfully.")

    print("---Starting fusion and gesture device...")
    fusion_process = Process(
        target=fusion_gesture_start,
        args=(gesture_queue, eye_queue, head_queue),  
        daemon=True
    )
    fusion_process.start()
    print("---Fusion and gesture device started successfully.")


    print("---Starting server...")
    user_manager = UserManager()
    print("---Server started successfully.")

    app.run(debug=False,port=5000)