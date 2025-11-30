#!/usr/bin/env python3
"""
Reliable UDP Client using:
- Sequence numbers
- Checksum system
- Retransmissions for loss/corruption
"""

import argparse
import socket
import threading
import time
import random

# ===========================
# CHECKSUM SYSTEM
# ===========================

def add_checksum(word):
    checksum = sum(ord(c) for c in word) % 256
    return f"{word}{checksum:02X}"

def verify_checksum(received_word):
    if len(received_word) < 2:
        return False, ""
    data = received_word[:-2]
    hex_val = received_word[-2:]
    try:
        recv = int(hex_val, 16)
    except:
        return False, ""
    calc = sum(ord(c) for c in data) % 256
    return calc == recv, data

# ===========================
# RELIABLE CLIENT
# ===========================

def run_client(server_ip, server_port, num_messages, interval):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2.0)

    msg = input("Enter a message to send: ")
    sets = msg.split()
    print(f"[CLIENT] You entered: {sets}")


    print(f"[RELIABLE CLIENT] Connected to {server_ip}:{server_port}")
    print(f"[RELIABLE CLIENT] Sending {num_messages} reliable packets...")
    print("-" * 60)

    sent = 0
    acked = 0

    for word in sets:

        # payload = user message
        payload = word

        # apply your checksum
        payload_cs = add_checksum(payload)

        # final packet: SEQ|DATA+CS
        packet = payload_cs.encode()

        while True:
            sock.sendto(packet, (server_ip, server_port))
            print(f"[CLIENT] Sent: {packet}")

            try:
                data = sock.recvfrom(2048)
                print(data)
                resp = data.decode()
                if resp == payload_cs[-2:]:
                    print(f"[CLIENT] ✓ Recieved valid checksum response: {resp}")
                    acked += 1
                    break
                else:
                    print(f"[CLIENT] ⚠ Unexpected or corrupted checksum: {resp}")

            except socket.timeout:
                print(f"[CLIENT] ⟳ Timeout -> Retransmitting msg")
                continue

        seq += 1
        sent += 1
        time.sleep(interval)

    print("\n" + "="*60)
    print("[CLIENT] Reliable Transmission Summary")
    print("="*60)
    print(f"Messages sent: {sent}")
    print(f"Acknowledged: {acked}")
    print(f"Loss/Corruption handled: {sent - acked}")
    print("="*60)

    sock.close()


def main():
    parser = argparse.ArgumentParser(description='Reliable UDP Client')
    parser.add_argument('--server-ip', default='127.0.0.1')
    parser.add_argument('--server-port', type=int, default=8888)
    parser.add_argument('--num-messages', type=int, default=10)
    parser.add_argument('--interval', type=float, default=1.0)

    args = parser.parse_args()
    run_client(args.server_ip, args.server_port, args.num_messages, args.interval)


if __name__ == '__main__':
    main()
#help