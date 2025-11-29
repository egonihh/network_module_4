#!/usr/bin/env python3
"""
Reliable UDP Server
- Responds with ACK:<seq> if checksum is valid
"""

import socket

SERVER_IP = '127.0.0.1'
SERVER_PORT = 8888

def verify_checksum(received_word):
    if '|' not in received_word:
        return False, ""
    data, cs_hex = received_word.rsplit('|', 1)
    try:
        recv = int(cs_hex, 16)
    except:
        return False, ""
    calc = sum(ord(c) for c in data) % 256
    return calc == recv, data

def main():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((SERVER_IP, SERVER_PORT))
    print(f"[SERVER] Listening on {SERVER_IP}:{SERVER_PORT}...")

    while True:
        data, addr = sock.recvfrom(2048)
        message = data.decode("utf-8", errors="replace")

        if '|' not in message:
            print(f"[SERVER] Malformed packet from {addr}: {message}")
            continue

        try:
            seq_str, payload_cs = message.split('|', 1)
            seq = int(seq_str)
        except ValueError:
            print(f"[SERVER] Invalid sequence: {message}")
            continue

        valid, payload = verify_checksum(payload_cs)
        if valid:
            print(f"[SERVER] ✅ Received valid seq {seq} payload: {payload}")
            sock.sendto(f"ACK:{seq}".encode(), addr)
        else:
            print(f"[SERVER] ❌ Corrupted packet seq {seq} from {addr}, ignoring")

if __name__ == '__main__':
    main()
