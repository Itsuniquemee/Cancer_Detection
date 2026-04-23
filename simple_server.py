#!/usr/bin/env python3
"""Ultra-simple HTTP server for CancerDetect Pro"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import json

class Handler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # Serve index_premium.html (new premium version)
            html_file = 'index_premium.html'
            if os.path.exists(html_file):
                with open(html_file, 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html; charset=utf-8')
                    self.end_headers()
                    self.wfile.write(f.read())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"File not found")
        elif self.path.startswith('/api/'):
            # Handle API calls
            if self.path == '/api/health':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'healthy'}).encode())
            elif self.path == '/api/model-info':
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                data = {
                    'name': 'Breast Cancer Detection Model',
                    'version': '2.0.0',
                    'accuracy': 0.9561,
                    'algorithm': 'Logistic Regression'
                }
                self.wfile.write(json.dumps(data).encode())
            else:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(b"API endpoint not found")
        else:
            # Serve static files (CSS, JS, images)
            return SimpleHTTPRequestHandler.do_GET(self)
    
    def log_message(self, format, *args):
        """Log message to console"""
        print(f"{self.client_address[0]} - {format%args}")

if __name__ == '__main__':
    os.chdir('/Users/manas/Maanas/BreastCancerDetectionWeb')
    server_address = ('127.0.0.1', 9000)
    httpd = HTTPServer(server_address, Handler)
    print("Server running on http://127.0.0.1:9000")
    print("Press Ctrl+C to stop")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped")
