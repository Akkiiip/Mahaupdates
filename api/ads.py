from http.server import BaseHTTPRequestHandler


ADS_TXT = "google.com, pub-2064611208436352, DIRECT, f08c47fec0942fa0"


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = ADS_TXT.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
