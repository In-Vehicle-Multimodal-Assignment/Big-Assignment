from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import os
import sys
import random
from flask_cors import CORS
from pydantic import BaseModel

app = Flask(__name__)
CORS(app)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 现在可以导入w目录下的a.py
#from whisper_large.main import audio_recognition, audio_start

print("Starting audio device...")
#audio_start() 
print("Audio device started successfully.")

app = Flask(__name__)
CORS(app)  # 启用跨域支持，允许所有来源请求

admins = {"alice", "bob"}
users = {"carol", "dave", "eve"}

class LoginRequest(BaseModel):
    username: str

@app.post("/login")
def login():
    data = request.get_json()  # 从请求中手动提取 JSON 数据
    if not data or "username" not in data:
        return jsonify(success=False, message="缺少用户名"), 400

    username = data["username"].strip()
    if username in admins:
        return jsonify(success=True, is_admin=True)
    elif username in users:
        return jsonify(success=True, is_admin=False)
    else:
        return jsonify(success=False, message="用户不存在")
    

# 模拟接口：返回数字类型结果
@app.route('/gesture-result')
def gesture_result():
    code = random.choice([4,2,3])  # 模拟返回值
    return jsonify(code=code)

# 返回结构化数据
@app.route('/voice-result')
def voice_result():
    code = random.choice([4,2,3])  # 模拟返回值
    return jsonify(code=code)

# 模拟接口：返回数字类型结果
@app.route('/head-result')
def head_result():
    code = random.choice([4,2,3])  # 模拟返回值
    return jsonify(code=code)

# 返回结构化数据
@app.route('/eye-result')
def eye_result():
    code = random.choice([4,2,3])  # 模拟返回值
    return jsonify(code=code)

@app.route('/start-record', methods=['POST'])
def start_record():
    data = request.get_json()
    if data.get("flag") == True:
        print("开始录音...")

        #result = audio_recognition()
        #print("录音结束，结果:", result)
        return jsonify(success=True)
    else:
        return jsonify(success=False), 400

if __name__ == '__main__':
    app.run(debug=True,port=5000)


