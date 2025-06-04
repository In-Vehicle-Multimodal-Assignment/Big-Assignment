from flask import Flask, request, jsonify
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)  # 启用跨域支持，允许所有来源请求

@app.route('/start-record', methods=['POST'])
def start_record():
    data = request.get_json()
    if data.get("flag") == True:
        print("开始录音...")

        # 模拟录音逻辑（3秒）
        time.sleep(3)

        print("录音结束，生成 wav 文件")
        return jsonify(success=True)
    else:
        return jsonify(success=False), 400

if __name__ == '__main__':
    app.run(debug=True)


