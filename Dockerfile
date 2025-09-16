FROM python:3.9-slim

# Set timezone to avoid interactive prompts
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=UTC

# Install required packages
RUN apt-get update && apt-get install -y \
    ffmpeg \
    sox \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create directories
RUN mkdir -p /app/sounds

# Copy Python SIP server
COPY sip_server.py /app/
COPY start.sh /start.sh
RUN chmod +x /start.sh

# Expose SIP and RTP ports
EXPOSE 5060/udp
EXPOSE 10000-10100/udp

# Set working directory
WORKDIR /app

# Start script
CMD ["/start.sh"]