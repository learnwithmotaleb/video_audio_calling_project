#!/bin/sh
# Prepare an Ubuntu VPS for LiveKit. Run once as root.
set -eu

cat > /etc/sysctl.d/90-livekit.conf <<EOF
net.core.rmem_max=5000000
net.core.wmem_max=5000000
EOF
sysctl --system > /dev/null

ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw allow 443/udp
ufw allow 3478/udp
ufw allow 5349/tcp
ufw allow 7881/tcp
ufw allow 7882/udp
ufw allow 30000:30100/udp
ufw --force enable
