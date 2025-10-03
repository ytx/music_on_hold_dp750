#!/usr/bin/env python3
"""
Lightweight SIP Server for Music On Hold
Simple implementation that responds to SIP INVITE with automatic Music On Hold
"""

import socket
import threading
import time
import random
import subprocess
import os
from datetime import datetime

class SimpleSIPServer:
    def __init__(self, host='0.0.0.0', port=5060, audio_file='/app/sounds/music.wav'):
        self.host = host
        self.port = port
        self.audio_file = audio_file
        self.active_calls = {}

    def log(self, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")

    def generate_call_id(self):
        return f"{random.randint(100000, 999999)}@moh-server"

    def generate_tag(self):
        return f"tag-{random.randint(10000, 99999)}"

    def send_response(self, sock, addr, response):
        try:
            sock.sendto(response.encode('utf-8'), addr)
            self.log(f"Sent response to {addr[0]}:{addr[1]}")
        except Exception as e:
            self.log(f"Error sending response: {e}")

    def create_sip_response(self, request_lines, status_code, status_text):
        """Create SIP response based on received request"""
        response_lines = [f"SIP/2.0 {status_code} {status_text}"]

        # Copy necessary headers from request
        for line in request_lines[1:]:
            if line.startswith(('Via:', 'From:', 'Call-ID:', 'CSeq:')):
                response_lines.append(line)
            elif line.startswith('To:'):
                # Add tag to To header if it's missing
                if 'tag=' not in line:
                    response_lines.append(f"{line};tag={self.generate_tag()}")
                else:
                    response_lines.append(line)

        # Add server headers
        response_lines.extend([
            f"Contact: <sip:moh@{self.host}:{self.port}>",
            "Content-Length: 0",
            "User-Agent: MoH-Server/1.0",
            ""
        ])

        return '\r\n'.join(response_lines)

    def create_sip_ok_with_sdp(self, request_lines, audio_port):
        """Create 200 OK response with SDP for audio streaming"""
        response_lines = [f"SIP/2.0 200 OK"]

        # Copy necessary headers from request
        for line in request_lines[1:]:
            if line.startswith(('Via:', 'From:', 'Call-ID:', 'CSeq:')):
                response_lines.append(line)
            elif line.startswith('To:'):
                if 'tag=' not in line:
                    response_lines.append(f"{line};tag={self.generate_tag()}")
                else:
                    response_lines.append(line)

        # SDP content
        sdp_content = f"""v=0
o=moh-server 123456 123456 IN IP4 {self.host}
s=Music On Hold
c=IN IP4 {self.host}
t=0 0
m=audio {audio_port} RTP/AVP 0
a=rtpmap:0 PCMU/8000
a=sendonly
"""

        # Add headers
        response_lines.extend([
            f"Contact: <sip:moh@{self.host}:{self.port}>",
            f"Content-Type: application/sdp",
            f"Content-Length: {len(sdp_content)}",
            "User-Agent: MoH-Server/1.0",
            "",
            sdp_content
        ])

        return '\r\n'.join(response_lines)

    def start_rtp_stream(self, target_ip, target_port, audio_file):
        """Start RTP audio stream using ffmpeg"""
        try:
            cmd = [
                'ffmpeg',
                '-re',  # Read input at native frame rate
                '-stream_loop', '-1',  # Loop indefinitely
                '-i', audio_file,
                '-acodec', 'pcm_mulaw',
                '-ar', '8000',
                '-ac', '1',
                '-f', 'rtp',
                f'rtp://{target_ip}:{target_port}'
            ]

            self.log(f"Starting RTP stream to {target_ip}:{target_port}")
            process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return process
        except Exception as e:
            self.log(f"Error starting RTP stream: {e}")
            return None

    def handle_invite(self, sock, addr, request_lines):
        """Handle SIP INVITE request"""
        self.log(f"Handling INVITE from {addr[0]}:{addr[1]}")

        # Send 180 Ringing
        ringing_response = self.create_sip_response(request_lines, 180, "Ringing")
        self.send_response(sock, addr, ringing_response)

        # Wait a moment before answering
        time.sleep(1)

        # Generate RTP port
        rtp_port = random.randint(10000, 10100)

        # Send 200 OK with SDP
        ok_response = self.create_sip_ok_with_sdp(request_lines, rtp_port)
        self.send_response(sock, addr, ok_response)

        # Extract Call-ID for tracking
        call_id = None
        for line in request_lines:
            if line.startswith('Call-ID:'):
                call_id = line.split(':', 1)[1].strip()
                break

        if call_id and os.path.exists(self.audio_file):
            # Start RTP stream
            rtp_process = self.start_rtp_stream(addr[0], rtp_port, self.audio_file)
            if rtp_process:
                self.active_calls[call_id] = rtp_process
                self.log(f"Started Music On Hold for call {call_id}")

    def handle_bye(self, sock, addr, request_lines):
        """Handle SIP BYE request"""
        self.log(f"Handling BYE from {addr[0]}:{addr[1]}")

        # Send 200 OK
        ok_response = self.create_sip_response(request_lines, 200, "OK")
        self.send_response(sock, addr, ok_response)

        # Stop RTP stream
        call_id = None
        for line in request_lines:
            if line.startswith('Call-ID:'):
                call_id = line.split(':', 1)[1].strip()
                break

        if call_id in self.active_calls:
            try:
                self.active_calls[call_id].terminate()
                del self.active_calls[call_id]
                self.log(f"Stopped Music On Hold for call {call_id}")
            except Exception as e:
                self.log(f"Error stopping RTP stream: {e}")

    def handle_request(self, sock, addr, data):
        """Handle incoming SIP request"""
        try:
            request = data.decode('utf-8')
            request_lines = request.split('\r\n')

            if not request_lines:
                return

            method = request_lines[0].split()[0]
            self.log(f"Received {method} from {addr[0]}:{addr[1]}")

            if method == 'INVITE':
                self.handle_invite(sock, addr, request_lines)
            elif method == 'BYE':
                self.handle_bye(sock, addr, request_lines)
            elif method == 'ACK':
                # ACK is fire-and-forget, no response needed
                self.log("ACK received - no response needed")
            elif method in ['REGISTER', 'OPTIONS']:
                # Send 200 OK for REGISTER/OPTIONS
                ok_response = self.create_sip_response(request_lines, 200, "OK")
                self.send_response(sock, addr, ok_response)
            else:
                # Send 501 Not Implemented for other methods
                not_impl_response = self.create_sip_response(request_lines, 501, "Not Implemented")
                self.send_response(sock, addr, not_impl_response)

        except Exception as e:
            self.log(f"Error handling request: {e}")

    def start_server(self):
        """Start the SIP server"""
        sock = None
        try:
            self.log(f"Starting SIP server on {self.host}:{self.port}")
            self.log(f"Audio file: {self.audio_file}")

            self.log("Creating UDP socket...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

            # Enable socket reuse
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self.log(f"Binding to {self.host}:{self.port}...")
            sock.bind((self.host, self.port))

            # Set a timeout to help with debugging
            sock.settimeout(1.0)

            self.log("SIP server started - waiting for connections...")
            self.log("Server is ready to receive SIP messages")

            packet_count = 0
            while True:
                try:
                    data, addr = sock.recvfrom(4096)
                    packet_count += 1
                    self.log(f"*** PACKET #{packet_count} RECEIVED from {addr[0]}:{addr[1]} ***")
                    self.log(f"Data length: {len(data)} bytes")
                    self.log(f"Raw data preview: {data[:100]}...")

                    # Handle each request in a separate thread
                    thread = threading.Thread(target=self.handle_request, args=(sock, addr, data))
                    thread.daemon = True
                    thread.start()

                except socket.timeout:
                    # This is normal - just continue waiting
                    continue
                except Exception as e:
                    self.log(f"ERROR in packet reception: {e}")
                    continue

        except Exception as e:
            self.log(f"FATAL ERROR in start_server: {e}")
            import traceback
            self.log(f"Traceback: {traceback.format_exc()}")
            raise
        except KeyboardInterrupt:
            self.log("Shutting down server...")
        finally:
            # Clean up active calls
            for call_id, process in self.active_calls.items():
                try:
                    process.terminate()
                except:
                    pass
            if sock:
                sock.close()
                self.log("Socket closed")

if __name__ == '__main__':
    server = SimpleSIPServer()
    server.start_server()