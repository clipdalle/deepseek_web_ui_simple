from flask import Flask, request, jsonify, Response
from openai import OpenAI
import os
import argparse
import json
from dotenv import load_dotenv


# 加载环境变量
# 初始化Openai客户端，从环境变量中读取您的API Key
from config import DEEPSEEK_API_KEY
ARK_API_URL = "https://ark.cn-beijing.volces.com/api/v3"
#MODEL_NAME = "deepseek-r1-250120" 
MODEL_NAME = "deepseek-v3-241226"


# 初始化 OpenAI 客户端
client = OpenAI(
    base_url=ARK_API_URL,
    api_key=DEEPSEEK_API_KEY,
)

app = Flask(__name__)

@app.route('/')
def serve_index():
    return app.send_static_file('index.html')

@app.route('/api/chat', methods=['POST', 'GET'])
def chat():
    if request.method == 'GET':
        user_message = request.args.get('message')
    else:
        data = request.json
        if not data or 'message' not in data:
            return jsonify({"error": "Missing message parameter"}), 400
        user_message = data.get('message', '')

    if not user_message or not user_message.strip():
        return jsonify({"error": "Empty message"}), 400

    try:
        def generate():
            try:
                stream = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "你是人工智能助手."},
                        {"role": "user", "content": user_message}
                    ],
                    stream=True
                )
                for chunk in stream:
                    if chunk.choices:
                        content = chunk.choices[0].delta.content
                        if content:
                            yield f"data: {json.dumps({'response': content})}\n\n"
                yield f"data: [DONE]\n\n"
            except Exception as e:
                error_message = {"error": f"Stream error: {str(e)}"}
                yield f"data: {json.dumps(error_message)}\n\n"
                yield f"data: [DONE]\n\n"

        response = Response(generate(), mimetype='text/event-stream')
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Connection'] = 'keep-alive'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        return jsonify({"error": f"API error: {str(e)}"}), 500

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run Flask app with custom port")
    parser.add_argument('--port', type=int, default=os.getenv("PORT", 8888), help="Port to run the app on")
    args = parser.parse_args()
    app.run(debug=True, host='0.0.0.0', port=args.port)