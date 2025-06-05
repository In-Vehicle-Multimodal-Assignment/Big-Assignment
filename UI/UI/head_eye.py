from flask import Flask, jsonify
import random
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 模拟接口：返回数字类型结果
@app.route('/head-result')
def fusion_result():
    code = random.choice([4,2,3])  # 模拟返回值
    return jsonify(code=code)

# 返回结构化数据
@app.route('/eye-result')
def fusion_result_structured():
    code = random.choice([4,2,3])  # 模拟返回值
    return jsonify(code=code)

if __name__ == '__main__':
    app.run(debug=True, port=5002)