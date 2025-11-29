#!/usr/bin/env python3
"""
UDP Proxy with simulated packet loss, corruption, and delay
- Client sends to proxy, proxy forwards to server
- Proxy may drop/corrupt/delay packets
"""

import socket
import random
import time

# Proxy listens to client
PROXY_IP = '127.0.0.1'
PROXY_PORT = 9999

# Server actual location
SERVER_IP = '127.0.0.1'
SERVER_PORT = 8888

# Error simulation
PACKET_LOSS_RATE = 0.2
PACKET_CORRUPT_RATE = 0.2
MAX_DELAY = 1.0

def maybe_corrupt(payload):
    if random.random() < PACKET_CORRUPT_RATE:
        i = random.randint(0, len(payload)-1)
        corrupted = payload[:i] + chr(random.randint(32,126)) + payload[i+1:]
        return corrupted
    return payload

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((PROXY_IP, PROXY_PORT))
    print(f"[PROXY] Listening on {PROXY_IP}:{PROXY_PORT}...")

    while True:
        data, addr = sock.recvfrom(2048)
        message = data.decode("utf-8", errors="replace")

        # Simulate packet loss
        if random.random() < PACKET_LOSS_RATE:
            print(f"[PROXY] Dropping packet from {addr}")
            continue

        # Simulate delay
        time.sleep(random.random() * MAX_DELAY)

        # Maybe corrupt
        message = maybe_corrupt(message)
        print(f"[PROXY] Forwarding packet from {addr} -> server: {message}")
        sock.sendto(message.encode(), (SERVER_IP, SERVER_PORT))

        # Also forward ACKs from server back to client
        sock.settimeout(0.1)
        try:
            ack_data, _ = sock.recvfrom(2048)
            sock.sendto(ack_data, addr)
        except socket.timeout:
            pass

if __name__ == '__main__':
    main()
