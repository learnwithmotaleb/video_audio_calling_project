#!/bin/sh
# Point the development stack at this Mac's current LAN IP. Run after changing network.
# Usage: scripts/set-node-ip.sh [ip]
set -eu

cd "$(dirname "$0")/.."

interface=$(/sbin/route -n get default | awk '/interface:/ { print $2 }')
ip=${1:-$(/usr/sbin/ipconfig getifaddr "$interface")}

sed -i '' \
  -e "s|^LIVEKIT_NODE_IP=.*|LIVEKIT_NODE_IP=$ip|" \
  -e "s|^LIVEKIT_PUBLIC_URL=.*|LIVEKIT_PUBLIC_URL=ws://$ip:7880|" \
  .env

docker compose up -d --no-deps livekit api

echo "LiveKit now uses $ip. Run the app on a phone with:"
echo "flutter run --dart-define=API_BASE_URL=http://$ip:8000"
