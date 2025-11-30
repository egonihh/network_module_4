#!/usr/bin/env python3
"""
Reliable UDP Server:
- Validates checksum
- Checks sequence numbers
- Sends ACKs
"""

import argparse
import socket

# ===========================
# CHECKSUM SYSTEM
# ===========================

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
# SERVER LOGIC
# ===========================

def run_server(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", port))

    print(f"[RELIABLE SERVER] Listening on port {port}")
    expected_seq = 1

    while True:
        data, addr = sock.recvfrom(65535)
        payload = data[0]

 #       try:
#          seq_str, payload = msg.split("|", 1)
#           seq = int(seq_str)
 #       except:
  #          print(f"[SERVER] Invalid packet: {msg}")
   #         continue

        print(f"\n[SERVER] Received packet: {payload}")

        # verify checksum
        strdata = str(payload)
        ok, clean_data = verify_checksum(strdata)

        if not ok:
            print("[SERVER] ❌ Checksum failed -> Ignoring packet")
            # Send ACK for last valid packet to trigger resend
            sock.sendto(strdata[-2:].encode, addr)
            continue

        if ok:
            print(f"[SERVER] ✓ Accepted packet: {clean_data} sending response {strdata[-2:]} ")
            sock.sendto(strdata[-2:].encode, addr)
            expected_seq += 1

        #else:
            # Out of order or duplicate
            #print(f"[SERVER] ⚠ Wrong order. Expected {expected_seq}, got {seq}")
            #sock.sendto(f"ACK:{expected_seq-1}".encode(), addr)


def main():
    parser = argparse.ArgumentParser(description='Reliable UDP Server')
    parser.add_argument('--port', type=int, default=9999)
    args = parser.parse_args()
    run_server(args.port)


if __name__ == '__main__':
    main()
