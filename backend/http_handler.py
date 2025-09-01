from handler import handler, load_models
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Load models on startup
print("Loading models on server startup...")
load_models()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy", "models_loaded": True})

@app.route('/process', methods=['POST'])
def process():
    try:
        data = request.get_json()
        result = handler({"input": data, "id": "http_request"})
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)