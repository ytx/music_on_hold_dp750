#!/usr/bin/env python3
"""
Simple UDP test to verify SIP server connection
"""

import socket
import sys

def test_udp_connection(server_ip="127.0.0.1", port=5060):
    """Test UDP connection to SIP server"""
    print(f"Testing UDP connection to {server_ip}:{port}...")

    try:
        # Create UDP socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(5)

        # Send test message
        message = b"UDP_TEST_MESSAGE"
        target = (server_ip, port)

        print(f"Sending test message to {target[0]}:{target[1]}")
        sock.sendto(message, target)

        print("Message sent. Waiting for response...")

        # Try to receive response
        try:
            data, addr = sock.recvfrom(1024)
            print(f"✓ Received response from {addr}: {data}")
            return True
        except socket.timeout:
            print("✗ No response received (timeout)")
            return False

    except Exception as e:
        print(f"✗ Error: {e}")
        return False
    finally:
        sock.close()

if __name__ == '__main__':
    # Get server IP from command line argument or default to localhost
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
    else:
        server_ip = "127.0.0.1"

    # Get port from command line argument or default to 5060
    if len(sys.argv) > 2:
        port = int(sys.argv[2])
    else:
        port = 5060

    test_udp_connection(server_ip, port)