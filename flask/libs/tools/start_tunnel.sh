#!/usr/bin/bash
echo "Starting tunnel"
if [ -z "$1" ]; then
  PORT="5000"
else
  PORT="$1"
fi
echo "--------------------------"
echo Port: $PORT


IP=$(wget -q -O - ipv4.icanhazip.com)

echo "your ip/pwd is: " $IP

npx localtunnel --port $PORT &

sleep(5)

echo "--------------------------"
echo "USE fg <enter> then ctrl-c to stop"
