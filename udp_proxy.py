#!/usr/bin/env python3
"""
UDP Proxy with configurable network impairments (loss, delay, corruption, reordering)
"""

import argparse
import random
import socket
import threading
import time
from scapy.all import IP, UDP, Raw, send
from scapy.layers.inet import UDP as UDP_Layer

class UDPProxy:
    def __init__(self, listen_port, target_ip, target_port, loss_rate=0.0,
                 max_delay=0.0, corruption_rate=0.0):
        self.listen_port = listen_port
        self.target_ip = target_ip
        self.target_port = target_port
        self.loss_rate = loss_rate
        self.max_delay = max_delay
        self.corruption_rate = corruption_rate

        # Dictionary to track client sessions: {(client_ip, client_port): last_seen_time}
        self.sessions = {}
        self.sessions_lock = threading.Lock()

        # Socket for receiving from clients
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.listen_socket.bind(('0.0.0.0', listen_port))

        # Socket for receiving responses from target
        self.response_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.response_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.response_socket.bind(('0.0.0.0', 0))  # Bind to any available port
        self.response_port = self.response_socket.getsockname()[1]

        print(f"[PROXY] Listening on port {listen_port}")
        print(f"[PROXY] Forwarding to {target_ip}:{target_port}")
        print(f"[PROXY] Loss rate: {loss_rate*100}%")
        print(f"[PROXY] Max delay: {max_delay}s")
        print(f"[PROXY] Corruption rate: {corruption_rate*100}%")
        print(f"[PROXY] Response listening port: {self.response_port}")

    def apply_impairments(self, data, src_ip, src_port, dst_ip, dst_port, from_client=True):
        """Apply network impairments and forward packet"""

        # Simulate packet loss
        if random.random() < self.loss_rate:
            print(f"[PROXY] LOST packet from {src_ip}:{src_port} -> {dst_ip}:{dst_port}")
            return

        # Simulate delay (with potential reordering)
        delay = random.uniform(0, self.max_delay) if self.max_delay > 0 else 0

        # Simulate corruption
        if random.random() < self.corruption_rate:
            data = self.corrupt_data(data)
            print(f"[PROXY] CORRUPTED packet from {src_ip}:{src_port} -> {dst_ip}:{dst_port}")

        if delay > 0:
            print(f"[PROXY] DELAYING packet by {delay:.2f}s from {src_ip}:{src_port} -> {dst_ip}:{dst_port}")
            threading.Timer(delay, self.forward_packet, args=(data, dst_ip, dst_port, from_client)).start()
        else:
            self.forward_packet(data, dst_ip, dst_port, from_client)

    def corrupt_data(self, data):
        """Corrupt random byte(s) in the data"""
        if len(data) == 0:
            return data

        data_list = bytearray(data)
        num_corruptions = max(1, len(data) // 10)  # Corrupt ~10% of bytes

        for _ in range(num_corruptions):
            pos = random.randint(0, len(data_list) - 1)
            data_list[pos] = random.randint(0, 255)

        return bytes(data_list)

    def forward_packet(self, data, dst_ip, dst_port, from_client=True):
        """Forward packet to destination"""
        if from_client:
            # Send to target from response_socket so replies come back there
            self.response_socket.sendto(data, (dst_ip, dst_port))
        else:
            # Send to client from listen_socket
            self.listen_socket.sendto(data, (dst_ip, dst_port))

    def handle_client_to_target(self):
        """Handle packets from clients to target"""
        while True:
            try:
                data, (client_ip, client_port) = self.listen_socket.recvfrom(65535)

                print(f"\n[PROXY] Received from client {client_ip}:{client_port}: {data[:50]}")

                # Register session
                with self.sessions_lock:
                    self.sessions[(client_ip, client_port)] = time.time()

                # Apply impairments and forward to target
                self.apply_impairments(data, client_ip, client_port,
                                     self.target_ip, self.target_port, from_client=True)

            except Exception as e:
                print(f"[PROXY] Error in client handler: {e}")

    def handle_target_to_client(self):
        """Handle responses from target back to clients"""
        while True:
            try:
                data, (src_ip, src_port) = self.response_socket.recvfrom(65535)

                print(f"\n[PROXY] Received response from target {src_ip}:{src_port}: {data[:50]}")

                # Find the most recent client session to send response to
                with self.sessions_lock:
                    if self.sessions:
                        # Get most recent client
                        client = max(self.sessions.items(), key=lambda x: x[1])[0]
                        client_ip, client_port = client

                        print(f"[PROXY] Routing response to client {client_ip}:{client_port}")

                        # Apply impairments and forward to client
                        self.apply_impairments(data, src_ip, src_port,
                                             client_ip, client_port, from_client=False)

            except Exception as e:
                print(f"[PROXY] Error in target handler: {e}")

    def start(self):
        """Start the proxy"""
        # Start thread for client->target
        client_thread = threading.Thread(target=self.handle_client_to_target, daemon=True)
        client_thread.start()

        # Start thread for target->client
        target_thread = threading.Thread(target=self.handle_target_to_client, daemon=True)
        target_thread.start()

        print("[PROXY] Proxy started. Press Ctrl+C to stop.")

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n[PROXY] Shutting down...")
            self.listen_socket.close()
            self.response_socket.close()


def main():
    parser = argparse.ArgumentParser(description='UDP Proxy with Network Impairments')
    parser.add_argument('--target-ip', required=True, help='Target server IP address')
    parser.add_argument('--target-port', type=int, required=True, help='Target server port')
    parser.add_argument('--listen-port', type=int, default=8888, help='Proxy listen port (default: 8888)')
    parser.add_argument('--loss', type=float, default=0.0, help='Packet loss probability (0.0-1.0, e.g., 0.05 for 5%%)')
    parser.add_argument('--delay', type=float, default=0.0, help='Maximum delay in seconds (e.g., 5.0 for 0-5s random delay)')
    parser.add_argument('--corruption', type=float, default=0.0, help='Corruption probability (0.0-1.0, e.g., 0.05 for 5%%)')

    args = parser.parse_args()

    # Validate arguments
    if not (0.0 <= args.loss <= 1.0):
        parser.error("Loss rate must be between 0.0 and 1.0")
    if not (0.0 <= args.corruption <= 1.0):
        parser.error("Corruption rate must be between 0.0 and 1.0")
    if args.delay < 0:
        parser.error("Delay must be non-negative")

    proxy = UDPProxy(
        listen_port=args.listen_port,
        target_ip=args.target_ip,
        target_port=args.target_port,
        loss_rate=args.loss,
        max_delay=args.delay,
        corruption_rate=args.corruption
    )

    proxy.start()


if __name__ == '__main__':
    main()
