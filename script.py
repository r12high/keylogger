import sys
import time

log_file = "log.txt"

def log_input(text):
    with open(log_file, 'a') as f:
        f.write(f"{time.ctime()}: {text}\n")
    print(f"Logged: {text}")

if __name__ == "__main__":
    print("Running data logger. Enter text (type 'exit' to stop):")
    while True:
        import http.server
import socketserver

PORT = 8000
Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()