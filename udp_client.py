#!/usr/bin/env python3
"""
Reliable UDP Client
- Sequence numbers
- Checksum system
- Retransmissions with maximum retry limit
"""

import argparse
import socket
import time

# ===========================
# CHECKSUM SYSTEM
# ===========================

def add_checksum(word: str) -> str:
    """Append 2-digit hex checksum separated by |"""
    checksum = sum(ord(c) for c in word) % 256
    return f"{word}|{checksum:02X}"

def verify_checksum(received_word: str) -> tuple[bool, str]:
    """Expect format: DATA|CS"""
    if '|' not in received_word:
        return False, ""
    data, cs_hex = received_word.rsplit('|', 1)
    try:
        recv = int(cs_hex, 16)
    except ValueError:
        return False, ""
    calc = sum(ord(c) for c in data) % 256
    return calc == recv, data

# ===========================
# RELIABLE CLIENT
# ===========================

def run_client(server_ip, server_port, num_messages, interval, max_retries=5):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(1.0)

    seq = 1
    sent = 0
    acked = 0

    print(f"[CLIENT] Sending {num_messages} reliable packets to {server_ip}:{server_port}")
    print("-" * 60)

    for _ in range(num_messages):
        payload = f"MSG{seq}"
        payload_cs = add_checksum(payload)
        packet = f"{seq}|{payload_cs}".encode()

        retries = 0
        while retries < max_retries:
            try:
                sock.sendto(packet, (server_ip, server_port))
                print(f"[CLIENT] Sent: {packet}")

                data, _ = sock.recvfrom(2048)
                resp = data.decode("utf-8", errors="replace")

                if resp == f"ACK:{seq}":
                    print(f"[CLIENT] ✓ ACK received for seq {seq}")
                    acked += 1
                    break
                else:
                    print(f"[CLIENT] ⚠ Unexpected ACK: {resp}")

            except socket.timeout:
                retries += 1
                print(f"[CLIENT] ⟳ Timeout -> Retransmitting seq {seq} ({retries}/{max_retries})")
            except ConnectionResetError:
                retries += 1
                print(f"[CLIENT] ⚠ Connection reset by server -> Retransmitting seq {seq} ({retries}/{max_retries})")
        else:
            print(f"[CLIENT] ❌ Failed to send seq {seq} after {max_retries} retries")

        seq += 1
        sent += 1
        time.sleep(interval)

    print("\n" + "="*60)
    print("[CLIENT] Reliable Transmission Summary")
    print("="*60)
    print(f"Messages sent: {sent}")
    print(f"Acknowledged: {acked}")
    print(f"Failed / Retransmissions exceeded: {sent - acked}")
    print("="*60)
    sock.close()

# ===========================
# MAIN
# ===========================

def main():
    parser = argparse.ArgumentParser(description='Reliable UDP Client')
    parser.add_argument('--server-ip', default='127.0.0.1')
    parser.add_argument('--server-port', type=int, default=8888)
    parser.add_argument('--num-messages', type=int, default=10)
    parser.add_argument('--interval', type=float, default=1.0)
    parser.add_argument('--max-retries', type=int, default=5)
    args = parser.parse_args()

    run_client(args.server_ip, args.server_port, args.num_messages, args.interval, args.max_retries)

if __name__ == '__main__':
    main()
