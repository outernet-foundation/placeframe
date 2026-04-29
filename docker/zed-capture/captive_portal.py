import socket
import struct
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

BIND_IP = "192.168.55.1"
TARGET = bytes([192, 168, 55, 1])
QTYPE_A = 1


def bind_with_retry(family, type_, addr):
    while True:
        s = socket.socket(family, type_)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(addr)
            return s
        except OSError as e:
            s.close()
            print(f"bind {addr} failed: {e}; retry in 5s", flush=True)
            time.sleep(5)


def dns_server():
    sock = bind_with_retry(socket.AF_INET, socket.SOCK_DGRAM, (BIND_IP, 53))
    while True:
        try:
            data, addr = sock.recvfrom(512)
            if len(data) < 12:
                continue
            pos = 12
            while pos < len(data) and data[pos] != 0:
                pos += data[pos] + 1
            pos += 1
            if pos + 4 > len(data):
                continue
            qtype = struct.unpack(">H", data[pos : pos + 2])[0]
            qend = pos + 4
            header = (
                data[:2]
                + b"\x81\x80"
                + data[4:6]
                + (b"\x00\x01" if qtype == QTYPE_A else b"\x00\x00")
                + b"\x00\x00\x00\x00"
            )
            question = data[12:qend]
            if qtype == QTYPE_A:
                answer = b"\xc0\x0c\x00\x01\x00\x01" + struct.pack(">I", 60) + b"\x00\x04" + TARGET
                sock.sendto(header + question + answer, addr)
            else:
                sock.sendto(header + question, addr)
        except Exception as e:
            print(f"dns error: {e}", flush=True)


BODY = (
    b"<!doctype html><meta charset=utf-8><title>ZED capture box</title>"
    b"<h1>ZED capture box</h1>"
    b"<p>This is the placeframe ZED capture rig. There is no sign-in. "
    b"You can dismiss the notification &mdash; the Capture Tool app talks "
    b"to the box directly, and other apps will continue to use wifi or "
    b"cellular as normal.</p>"
)


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(BODY)))
        self.end_headers()
        self.wfile.write(BODY)

    def log_message(self, *a):
        pass


threading.Thread(target=dns_server, daemon=True).start()
while True:
    try:
        HTTPServer((BIND_IP, 80), H).serve_forever()
    except OSError as e:
        print(f"http bind failed: {e}; retry in 5s", flush=True)
        time.sleep(5)
