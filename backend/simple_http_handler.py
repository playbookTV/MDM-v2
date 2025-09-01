from handler import handler, load_models
import http.server
import socketserver
import json
import urllib.parse

# Load models on startup
print("Loading models on server startup...")
load_models()

class AIHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {"status": "healthy", "models_loaded": True}
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        if self.path == '/process':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode())
                result = handler({"input": data, "id": "http_request"})
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(result).encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                error_response = {"status": "error", "error": str(e)}
                self.wfile.write(json.dumps(error_response).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    PORT = 8000
    with socketserver.TCPServer(("", PORT), AIHandler) as httpd:
        print(f"🚀 AI Server running at http://0.0.0.0:{PORT}")
        print(f"📍 External URL: https://i4mc5gqc7sepzc-8000.proxy.runpod.net")
        httpd.serve_forever()