import sys
import time

log_file = "log.txt"

def log_input(text):
    with open(log_file, 'a') as f:
        f.write(f"{time.ctime()}: {text}\n")
    print(f"Logged: {text}")

if __name__ == "__main__":
    if __name__ == "__main__":
    print("Running data logger. Enter text (type 'exit' to stop):")
    import http.server
    import socketserver
    import threading

    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), Handler)
    
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    print(f"Serving at port {PORT}")

    while True:
        try:
            user_in = input("> ")
            if user_in.lower() == 'exit':
                break
            log_input(user_in)
        except EOFError:
            break