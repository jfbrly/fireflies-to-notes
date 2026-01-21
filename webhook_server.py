#!/usr/bin/env python3
"""
Webhook server for Fireflies.ai notifications.
Automatically processes new transcripts when meetings end.

Requirements: flask (pip install flask requests)
Run on macOS only.
"""

from flask import Flask, request, jsonify
import hmac
import hashlib
import os
from fireflies_notes import process_transcript

app = Flask(__name__)

# Optional: Set this to verify webhook signatures
WEBHOOK_SECRET = os.environ.get("FIREFLIES_WEBHOOK_SECRET", "")

def verify_signature(payload: bytes, signature: str) -> bool:
    """Verify Fireflies webhook signature."""
    if not WEBHOOK_SECRET:
        return True  # Skip verification if no secret set
    
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected}", signature)

@app.route("/webhook/fireflies", methods=["POST"])
def fireflies_webhook():
    """Handle Fireflies webhook notifications."""
    
    # Verify signature if secret is set
    signature = request.headers.get("x-hub-signature", "")
    if WEBHOOK_SECRET and not verify_signature(request.data, signature):
        return jsonify({"error": "Invalid signature"}), 401
    
    data = request.json
    print(f"📬 Received webhook: {data}")
    
    event_type = data.get("eventType", "")
    meeting_id = data.get("meetingId", "")
    
    if event_type == "Transcription completed" and meeting_id:
        print(f"🎯 Processing transcript: {meeting_id}")
        success = process_transcript(meeting_id)
        return jsonify({"processed": success, "meetingId": meeting_id})
    
    return jsonify({"status": "ignored", "eventType": event_type})

@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    print(f"🚀 Starting webhook server on port {port}")
    print(f"📌 Webhook URL: http://localhost:{port}/webhook/fireflies")
    print(f"💡 Use ngrok to expose: ngrok http {port}")
    app.run(host="0.0.0.0", port=port, debug=True)
