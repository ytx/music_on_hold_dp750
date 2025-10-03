#!/usr/bin/env python3
"""
SIP Client Test Script for Music On Hold Server
Tests basic SIP functionality without requiring registration
"""

import socket
import time
import random
import threading
from datetime import datetime

class SimpleSIPClient:
    def __init__(self, server_host='192.168.52.3', server_port=5060, local_port=5061):
        self.server_host = server_host
        self.server_port = server_port
        self.local_port = local_port
        self.call_id = None
        self.branch = None
        self.tag = None
        self.socket = None

    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] CLIENT: {message}")

    def generate_call_id(self):
        return f"{random.randint(100000, 999999)}@test-client"

    def generate_branch(self):
        return f"z9hG4bK{random.randint(100000, 999999)}"

    def generate_tag(self):
        return f"tag-{random.randint(10000, 99999)}"

    def create_invite(self, target_number="123"):
        """Create SIP INVITE message"""
        self.call_id = self.generate_call_id()
        self.branch = self.generate_branch()
        self.tag = self.generate_tag()

        local_ip = self.get_local_ip()

        invite = f"""INVITE sip:{target_number}@{self.server_host}:{self.server_port} SIP/2.0
Via: SIP/2.0/UDP {local_ip}:{self.local_port};branch={self.branch}
From: <sip:testclient@{local_ip}:{self.local_port}>;tag={self.tag}
To: <sip:{target_number}@{self.server_host}:{self.server_port}>
Call-ID: {self.call_id}
CSeq: 1 INVITE
Contact: <sip:testclient@{local_ip}:{self.local_port}>
Content-Type: application/sdp
Content-Length: 142
User-Agent: TestSIPClient/1.0

v=0
o=testclient 123456 123456 IN IP4 {local_ip}
s=Test Call
c=IN IP4 {local_ip}
t=0 0
m=audio 12000 RTP/AVP 0
a=rtpmap:0 PCMU/8000

"""
        return invite.replace('\n', '\r\n')

    def create_ack(self, response_lines):
        """Create SIP ACK message"""
        local_ip = self.get_local_ip()

        # Extract To header from response to get the tag
        to_header = None
        for line in response_lines:
            if line.startswith('To:'):
                to_header = line
                break

        ack = f"""ACK sip:123@{self.server_host}:{self.server_port} SIP/2.0
Via: SIP/2.0/UDP {local_ip}:{self.local_port};branch={self.branch}
From: <sip:testclient@{local_ip}:{self.local_port}>;tag={self.tag}
{to_header}
Call-ID: {self.call_id}
CSeq: 1 ACK
Content-Length: 0

"""
        return ack.replace('\n', '\r\n')

    def create_bye(self, response_lines):
        """Create SIP BYE message"""
        local_ip = self.get_local_ip()

        # Extract To header from response
        to_header = None
        for line in response_lines:
            if line.startswith('To:'):
                to_header = line
                break

        bye = f"""BYE sip:123@{self.server_host}:{self.server_port} SIP/2.0
Via: SIP/2.0/UDP {local_ip}:{self.local_port};branch={self.generate_branch()}
From: <sip:testclient@{local_ip}:{self.local_port}>;tag={self.tag}
{to_header}
Call-ID: {self.call_id}
CSeq: 2 BYE
Content-Length: 0

"""
        return bye.replace('\n', '\r\n')

    def get_local_ip(self):
        """Get local IP address"""
        try:
            # Connect to a remote address to determine local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            return "127.0.0.1"

    def send_message(self, message):
        """Send SIP message to server"""
        try:
            self.socket.sendto(message.encode('utf-8'), (self.server_host, self.server_port))
            self.log(f"Sent message to {self.server_host}:{self.server_port}")
            print("--- Sent Message ---")
            print(message)
            print("--- End Message ---")
        except Exception as e:
            self.log(f"Error sending message: {e}")

    def receive_response(self, timeout=10):
        """Receive SIP response from server"""
        try:
            self.socket.settimeout(timeout)
            data, addr = self.socket.recvfrom(4096)
            response = data.decode('utf-8')
            self.log(f"Received response from {addr[0]}:{addr[1]}")
            print("--- Received Response ---")
            print(response)
            print("--- End Response ---")
            return response.split('\r\n')
        except socket.timeout:
            self.log("Timeout waiting for response")
            return None
        except Exception as e:
            self.log(f"Error receiving response: {e}")
            return None

    def test_options(self):
        """Test SIP OPTIONS method"""
        self.log("Testing SIP OPTIONS...")

        local_ip = self.get_local_ip()
        call_id = self.generate_call_id()
        branch = self.generate_branch()

        options = f"""OPTIONS sip:{self.server_host}:{self.server_port} SIP/2.0
Via: SIP/2.0/UDP {local_ip}:{self.local_port};branch={branch}
From: <sip:testclient@{local_ip}:{self.local_port}>;tag={self.generate_tag()}
To: <sip:{self.server_host}:{self.server_port}>
Call-ID: {call_id}
CSeq: 1 OPTIONS
Content-Length: 0
User-Agent: TestSIPClient/1.0

"""
        self.send_message(options.replace('\n', '\r\n'))
        response = self.receive_response()

        if response and response[0].startswith('SIP/2.0 200'):
            self.log("✅ OPTIONS test PASSED - Server is responding")
            return True
        else:
            self.log("❌ OPTIONS test FAILED")
            return False

    def test_invite_call(self, target_number="123", call_duration=10):
        """Test SIP INVITE call flow"""
        self.log(f"Testing SIP INVITE call to {target_number}...")

        # Send INVITE
        invite = self.create_invite(target_number)
        self.send_message(invite)

        # Wait for responses
        responses_received = []
        start_time = time.time()

        while time.time() - start_time < 30:  # Wait up to 30 seconds
            response = self.receive_response(5)
            if not response:
                continue

            responses_received.append(response)
            status_line = response[0]

            if '180 Ringing' in status_line:
                self.log("✅ Received 180 Ringing")
            elif '200 OK' in status_line:
                self.log("✅ Received 200 OK - Call answered!")

                # Send ACK
                ack = self.create_ack(response)
                self.send_message(ack)

                # Wait for specified duration to listen to music
                self.log(f"Listening to Music On Hold for {call_duration} seconds...")
                time.sleep(call_duration)

                # Send BYE to end call
                bye = self.create_bye(response)
                self.send_message(bye)

                # Wait for BYE response
                bye_response = self.receive_response(5)
                if bye_response and '200 OK' in bye_response[0]:
                    self.log("✅ Call ended successfully")
                    return True
                break
            elif '4' in status_line[8] or '5' in status_line[8] or '6' in status_line[8]:
                self.log(f"❌ Call failed: {status_line}")
                break

        self.log("❌ INVITE test FAILED or incomplete")
        return False

    def run_tests(self):
        """Run all SIP tests"""
        self.log("Starting SIP server tests...")
        self.log(f"Target server: {self.server_host}:{self.server_port}")

        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('0.0.0.0', self.local_port))
            self.log(f"Local socket bound to port {self.local_port}")

            # Test 1: OPTIONS
            print("\n" + "="*50)
            print("TEST 1: SIP OPTIONS")
            print("="*50)
            options_success = self.test_options()

            # Test 2: INVITE Call
            print("\n" + "="*50)
            print("TEST 2: SIP INVITE CALL")
            print("="*50)
            if options_success:
                invite_success = self.test_invite_call("123", 5)
            else:
                self.log("Skipping INVITE test due to OPTIONS failure")
                invite_success = False

            # Summary
            print("\n" + "="*50)
            print("TEST SUMMARY")
            print("="*50)
            self.log(f"OPTIONS test: {'✅ PASS' if options_success else '❌ FAIL'}")
            self.log(f"INVITE test: {'✅ PASS' if invite_success else '❌ FAIL'}")

            if options_success and invite_success:
                self.log("🎉 All tests PASSED! SIP server is working correctly.")
            else:
                self.log("⚠️  Some tests FAILED. Check server configuration.")

        except Exception as e:
            self.log(f"Test setup error: {e}")
        finally:
            if self.socket:
                self.socket.close()

def main():
    import sys

    print("SIP Client Test Script")
    print("======================")

    # Get server IP from command line argument or default to localhost
    if len(sys.argv) > 1:
        server_ip = sys.argv[1]
    else:
        server_ip = "127.0.0.1"

    print(f"Testing server at {server_ip}")
    print()

    client = SimpleSIPClient(server_host=server_ip)
    client.run_tests()

if __name__ == '__main__':
    main()