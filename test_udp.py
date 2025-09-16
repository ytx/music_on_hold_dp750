#!/usr/bin/env python3
"""
Simple UDP test to verify Docker port forwarding
"""

import socket
import time

def test_udp_connection():
    """Test UDP connection to Docker container"""
    print("Testing UDP connection to Docker container...")

    try:
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)

        # Send test message
        message = b"UDP_TEST_MESSAGE"
        target = ("127.0.0.1", 5060)

        print(f"Sending test message to {target[0]}:{target[1]}")
        sock.sendto(message, target)

        print("Message sent. Waiting for response...")

        # Try to receive response
        try:
            data, addr = sock.recvfrom(1024)
            print(f"Received response from {addr}: {data}")
            return True
        except socket.timeout:
            print("No response received (timeout)")
            return False

    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        sock.close()

if __name__ == '__main__':
    test_udp_connection()