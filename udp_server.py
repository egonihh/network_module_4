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
    last_acked = 0
    received = {}  # store accepted payloads by seq
    total_messages = None

    while True:
        data, addr = sock.recvfrom(65535)
        # `data` is bytes; decode it to a str so slicing and checksum work correctly
        payload = data.decode('utf-8', errors='replace')

 #       try:
#          seq_str, payload = msg.split("|", 1)
#           seq = int(seq_str)
 #       except:
  #          print(f"[SERVER] Invalid packet: {msg}")
   #         continue

        print(f"\n[SERVER] Received packet: {payload}")

        # Expect packet format: "seq/total|DATA+CS"
        try:
            header, body = payload.split("|", 1)
            seq_str, total_str = header.split("/", 1)
            seq = int(seq_str)
            total = int(total_str)
        except Exception:
            print("[SERVER] ⚠ Invalid packet header -> Ignoring")
            continue

        # remember total for end-of-transmission detection
        if total_messages is None:
            total_messages = total

        # verify checksum on the body (DATA+CS)
        ok, clean_data = verify_checksum(body)

        if not ok:
            print("[SERVER] ❌ Checksum failed -> Ignoring packet")
            # Re-ACK last valid sequence so client can retransmit
            sock.sendto(f"ACK:{last_acked}".encode(), addr)
            continue

        # valid checksum
        if seq < expected_seq:
            # duplicate packet (already received)
            print(f"[SERVER] ↺ Duplicate packet seq {seq} -> re-ACKing")
            sock.sendto(f"ACK:{seq}".encode(), addr)
            continue

        if seq == expected_seq:
            # in-order packet -> accept
            print(f"[SERVER] ✓ Accepted packet {seq}: {clean_data}")
            received[seq] = clean_data
            last_acked = seq
            sock.sendto(f"ACK:{seq}".encode(), addr)
            expected_seq += 1

            # check if we've received the entire message
            if total_messages is not None and expected_seq > total_messages:
                # reconstruct full message in order
                parts = [received.get(i, "") for i in range(1, total_messages + 1)]
                full_message = " ".join(parts)
                print(f"\n[SERVER] === Full message reconstructed ===\n{full_message}\n")
                # reset for next transmission
                expected_seq = 1
                last_acked = 0
                received.clear()
                total_messages = None
            continue

        # seq > expected_seq -> out-of-order: ask client to resend last accepted
        print(f"[SERVER] ⚠ Out of order packet. Expected {expected_seq}, got {seq} -> re-ACKing {last_acked}")
        sock.sendto(f"ACK:{last_acked}".encode(), addr)


def main():
    parser = argparse.ArgumentParser(description='Reliable UDP Server')
    parser.add_argument('--port', type=int, default=9999)
    args = parser.parse_args()
    run_server(args.port)


if __name__ == '__main__':
    main()
