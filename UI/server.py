from flask import Flask, request, jsonify
from flask_cors import CORS
import time
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 现在可以导入w目录下的a.py
#from whisper_large.main import audio_recognition, audio_start

print("Starting audio device...")
#audio_start() 
print("Audio device started successfully.")

app = Flask(__name__)
CORS(app)  # 启用跨域支持，允许所有来源请求

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


