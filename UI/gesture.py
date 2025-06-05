from flask import Flask, jsonify
import random
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 模拟接口：返回数字类型结果
@app.route('/fusion-result')
def fusion_result():
    code = random.choice([4,2,3])  # 模拟返回值
    return jsonify(code=code)

# 返回结构化数据
@app.route('/fusion-result-structured')
def fusion_result_structured():
    result = random.choice([
        {"type": "ac", "message": "打开空调"},
        {"type": "fatigue", "message": "驾驶员疲劳，请注意休息"}
    ])
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
