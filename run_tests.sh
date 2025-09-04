#!/bin/bash

# Exit if any command fails
set -e

echo "Starting FastAPI server..."
uvicorn app:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

# Give server time to start
sleep 3

echo
echo "=== Checking health endpoint ==="
curl http://127.0.0.1:8000/health
echo -e "\n"

echo "=== Listing available agents ==="
curl http://127.0.0.1:8000/agents
echo -e "\n"

echo "=== Sending basic chat message ==="
curl -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"say hello","agent":"general","stream":false}'
echo -e "\n"

echo "=== Streaming request (count to five) ==="
# Capture headers and body separately
response=$(mktemp)
headers=$(mktemp)
curl -N -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"count to five","agent":"general","stream":true}' \
  -D "$headers"


# Extract the X-Conversation-Id from headers
conversation_id=$(grep -i "X-Conversation-Id:" "$headers" | awk '{print $2}' | tr -d '\r')

echo "Captured Conversation ID: $conversation_id"
echo

echo "=== Continuing conversation to ten ==="
curl -N -s -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\":\"and now continue to ten\",\"agent\":\"general\",\"stream\":true,\"conversation_id\":\"$conversation_id\"}"
echo -e "\n"

# Stop the uvicorn server
echo "Stopping server..."
kill $UVICORN_PID
