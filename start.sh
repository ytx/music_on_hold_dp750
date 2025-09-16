#!/bin/bash

set -e

echo "Music On Hold Server Starting..."

# Convert MP3 to WAV format suitable for RTP streaming
if [ -f "/music.mp3" ]; then
    echo "Converting MP3 to WAV format (8kHz, mono, PCM)..."
    ffmpeg -i /music.mp3 -ar 8000 -ac 1 -c:a pcm_s16le -f wav /app/sounds/music.wav -y

    if [ $? -eq 0 ]; then
        echo "Audio conversion completed successfully"
        ls -la /app/sounds/
        echo "Audio file info:"
        ffprobe /app/sounds/music.wav 2>&1 | grep -E "(Duration|Stream|Audio)" || true
    else
        echo "Error: Audio conversion failed"
        exit 1
    fi
else
    echo "Error: No music file found at /music.mp3"
    echo "Please mount your MP3 file to /music.mp3"
    exit 1
fi

echo "Starting lightweight SIP server..."
cd /app
exec python3 sip_server.py