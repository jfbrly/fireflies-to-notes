#!/bin/bash
# Auto-trigger setup for Fireflies to Apple Notes
# Run this on your Mac

set -e

echo "🔧 Fireflies Auto-Trigger Setup"
echo "================================"

# Check dependencies
command -v python3 >/dev/null || { echo "❌ python3 required"; exit 1; }
command -v pip3 >/dev/null || { echo "❌ pip3 required"; exit 1; }

# Install Python deps
echo "📦 Installing Python dependencies..."
pip3 install requests flask --quiet

# Install ngrok if needed
if ! command -v ngrok &> /dev/null; then
    echo "📦 Installing ngrok..."
    if command -v brew &> /dev/null; then
        brew install ngrok
    else
        echo "❌ Please install ngrok: https://ngrok.com/download"
        exit 1
    fi
fi

# Check for ngrok auth
if ! ngrok config check &> /dev/null; then
    echo ""
    echo "⚠️  ngrok not authenticated. Get your free authtoken from:"
    echo "   https://dashboard.ngrok.com/get-started/your-authtoken"
    echo ""
    read -p "Paste your ngrok authtoken: " NGROK_TOKEN
    ngrok config add-authtoken "$NGROK_TOKEN"
fi

# Get or create static domain
echo ""
echo "📌 Setting up static ngrok domain..."
echo "   Go to: https://dashboard.ngrok.com/domains"
echo "   Click 'New Domain' to get a free static domain"
echo "   (looks like: something-random-name.ngrok-free.app)"
echo ""
read -p "Paste your ngrok static domain: " NGROK_DOMAIN

# Get Fireflies API key
echo ""
read -p "Paste your Fireflies API key: " FIREFLIES_KEY

# Create env file
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cat > "$SCRIPT_DIR/.env" << EOF
export FIREFLIES_API_KEY="$FIREFLIES_KEY"
export NGROK_DOMAIN="$NGROK_DOMAIN"
EOF

echo "✅ Created .env file"

# Create launcher script
cat > "$SCRIPT_DIR/start.sh" << 'LAUNCHER'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/.env"

# Start webhook server in background
echo "🚀 Starting webhook server..."
python3 "$SCRIPT_DIR/webhook_server.py" &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Start ngrok with static domain
echo "🌐 Starting ngrok tunnel..."
ngrok http 5050 --domain="$NGROK_DOMAIN" &
NGROK_PID=$!

echo ""
echo "✅ Running! Webhook URL: https://$NGROK_DOMAIN/webhook/fireflies"
echo ""
echo "Press Ctrl+C to stop"

trap "kill $SERVER_PID $NGROK_PID 2>/dev/null" EXIT
wait
LAUNCHER
chmod +x "$SCRIPT_DIR/start.sh"

# Create LaunchAgent for auto-start
PLIST_PATH="$HOME/Library/LaunchAgents/com.fireflies.notes.plist"
cat > "$PLIST_PATH" << PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.fireflies.notes</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$SCRIPT_DIR/start.sh</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$SCRIPT_DIR/output.log</string>
    <key>StandardErrorPath</key>
    <string>$SCRIPT_DIR/error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
</dict>
</plist>
PLIST

echo ""
echo "============================================"
echo "✅ Setup complete!"
echo ""
echo "📌 Your webhook URL:"
echo "   https://$NGROK_DOMAIN/webhook/fireflies"
echo ""
echo "🔗 Add this URL to Fireflies:"
echo "   1. Go to https://app.fireflies.ai/settings"
echo "   2. Click 'Developer Settings' tab"
echo "   3. Paste the webhook URL above"
echo "   4. Save"
echo ""
echo "🚀 To start manually:  ./start.sh"
echo "🔄 To auto-start on login:"
echo "   launchctl load ~/Library/LaunchAgents/com.fireflies.notes.plist"
echo ""
