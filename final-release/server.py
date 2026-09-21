import http.server, socketserver, os

class Handler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        if self.path.endswith('.exe'):
            self.send_header('Content-Type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(self.path)}"')
        super().end_headers()

os.chdir('/home/user/web-app/final-release')
with socketserver.TCPServer(("0.0.0.0", 8000), Handler) as httpd:
    print("Serving at 0.0.0.0:8000 - Aniner EXE Download Ready")
    httpd.serve_forever()
