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

class LoginRequest(BaseModel):
    username: str


current_user = None
user_manager = None

login_ac = 0
login_music = 0



@app.post("/login")
def login():
    global eye_queue, head_queue, gesture_queue, current_user, user_manager, login_ac, login_music
    data = request.get_json()
    if not data or "username" not in data:
        return jsonify(success=False, message="缺少用户名"), 400
    
    username = data["username"].strip()
    current_user = username
    print(f"登录用户: {username}")
    while not gesture_queue.empty():
        gesture_queue.get()  
    while not eye_queue.empty():
        eye_queue.get()  
    while not head_queue.empty():
        head_queue.get()
    user_data = user_manager.authenticate(username)
    login_ac = user_data[4]
    login_music = user_data[5]
    if user_data[1]:
        return jsonify(success=True, is_admin=True)
    else:
        return jsonify(success=True, is_admin=False)
    
gesture_number = 0
voice_number = 0
head_number = 0
eye_number = 0

def translate_gesture(label):
    if label == 'fist':
        return 7
    elif label == 'palm':
        return 4
    elif label == 'like':
        return 8
    elif label == 'dislike':
        return 9
    elif label == 'peace':
        return 3
    elif label == 'one':
        return 6
    elif label == 'three':
        return 12
    elif label == 'four':
        return 13
    else:
        return 0

def translate_eye(label):
    if label == 'CENTER':
        return 10
    elif label == '':
        return 0
    else:
        return 11
    
def translate_head(label):
    if label == 'NOD':
        return 8
    elif label == 'SHAKE':
        return 9
    elif label == 'NO_FACE':
        return 2
    else:
        return 0

@app.route('/login-result')
def login_result():
    global login_ac, login_music
    current_label = 0
    if login_ac:
        current_label = 14
        login_ac = 0
    elif login_music:
        current_label = 15
        login_music = 0
    return jsonify(code=current_label)

@app.route('/gesture-result')
def gesture_result():
    global gesture_number
    try:
        current_label = gesture_queue.get_nowait()  # 非阻塞读取
        #print(f"当前手势: {current_label}")
    except:
        current_label = ""
    gesture_number = translate_gesture(current_label) 
    return jsonify(code=gesture_number)

@app.route('/voice-result')
def voice_result():
    global voice_number
    voice_code = voice_number
    if voice_code:
        voice_number = 0
    return jsonify(code=voice_code)

@app.route('/head-result')
def head_result():
    global head_number
    try:
        current_label = head_queue.get_nowait()  # 非阻塞读取
        #print(f"当前头部动作: {current_label}")
    except:
        current_label = ""
    head_number = translate_head(current_label)
    return jsonify(code=head_number)


@app.route('/eye-result')
def eye_result():
    global eye_number
    try:
        current_eye_label = eye_queue.get_nowait()  # 非阻塞读取
        #print(f"眼部持续位置: {current_eye_label}")
    except:
        current_eye_label = ""
    eye_number = translate_eye(current_eye_label)
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


@app.route("/saveResult", methods=["POST"])
def save_result():
    global current_user, user_manager
    data = request.get_json()
    print(data['message'])
    user_manager.update_log_history(current_user, data['message'])
    return jsonify({"status": "success"})






import json
import requests
url = "https://api.siliconflow.cn/v1/chat/completions"
headers = {
    "Authorization": "Bearer sk-ddlgzbwkuxqojvfxpyylmwhcgnyrvxswoplcfekdzffsclmq",
    "Content-Type": "application/json"
}

def personalized_service_start():
    global user_manager, url, headers 
    user_list = user_manager.get_all_usernames()
    for user in user_list:
        if user == "admin":
            continue
        print(f"正在处理用户: {user}")
        user_data = user_manager.get_user(user)
        current_log = user_data['log_history'] or ''
        payload = {
            "model": "deepseek-ai/DeepSeek-R1",
            "messages": [
                {
                    "role": "user",
                    "content": f"""
                        请严格按照以下规则分析用户日志：
                        ---
                        分析目标：判断用户是否存在以下4种行为倾向（1=存在，0=不存在）
                        1. 容易疲劳
                        2. 容易分心（如不注视前方）
                        3. 喜欢开空调
                        4. 喜欢开音乐

                        分析材料：
                        {current_log}

                        输出要求：
                        - 仅输出4位连续数字，分别对应上述4种倾向
                        - 禁止包含任何其他文字，禁止输出分析过程！我只要结果！

                        现在请直接输出4位数的结果：
                    """
                }
            ],
            "stream": False,
            "max_tokens": 512,
            "thinking_budget": 4096,
            "response_format": {"type": "text"},
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "description": "<string>",
                        "name": "<string>",
                        "parameters": {},
                        "strict": False
                    }
                }
            ]
        }
        # print(f"{payload['messages'][0]['content']}")
        while True:
            response = requests.request("POST", url, json=payload, headers=headers)
            response_data = json.loads(response.text)
            content = response_data["choices"][0]["message"]["content"]
            content = list(content.strip().replace("\\n", "\n"))
            print(content)
            content = [int(c) for c in content]
            print(content)
            if len(content) == 4:
                break
        print(user_manager.update_user_tendencies(user,content))
        


def main():
    global user_manager
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

    print("---Starting personalized service...")
    personalized_service_start()
    print("---Personalized service started successfully.")

    app.run(debug=False,port=5000)

if __name__ == '__main__':
    main()