#!/bin/bash
# test_motors.sh
# Quick test script to send manual motor commands to the Arduino via serial.
# Run this on the Raspberry Pi when the Arduino is connected via USB.
# Usage: bash test_motors.sh

PORT="${1:-/dev/ttyACM0}"

echo "============================================"
echo " Soccer Bot Motor Test Script"
echo " Target port: $PORT"
echo "============================================"

if [ ! -e "$PORT" ]; then
  echo "ERROR: Port $PORT not found. Is the Arduino plugged in?"
  echo "Available ports:"
  ls /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
  exit 1
fi

send_cmd() {
  echo -n "$1" > "$PORT"
  echo "Sent: $1 ($2)"
  sleep "$3"
}

# Set baud rate
stty -F "$PORT" 9600 raw

echo ""
echo "Testing motors..."
send_cmd "F" "Forward"  2
send_cmd "S" "Stop"     1
send_cmd "B" "Backward" 2
send_cmd "S" "Stop"     1
send_cmd "L" "Left"     1
send_cmd "S" "Stop"     1
send_cmd "R" "Right"    1
send_cmd "S" "Stop"     0.5

echo ""
echo "Motor test complete. Motors stopped."
