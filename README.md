# Fireflies to Apple Notes

Automatically sync Fireflies.ai action items to your Apple Notes "TODO and Work!" note.

## Setup (on your Mac)

1. **Install dependencies:**
   ```bash
   pip3 install requests flask
   ```

2. **Test the connection:**
   ```bash
   python3 fireflies_notes.py --test
   ```

3. **Manual sync (fetch latest meeting):**
   ```bash
   python3 fireflies_notes.py --recent 1
   ```

## Auto-trigger after meetings

### Option A: Webhook (real-time)

1. Install ngrok: `brew install ngrok`

2. Start the webhook server:
   ```bash
   python3 webhook_server.py
   ```

3. In another terminal, expose it:
   ```bash
   ngrok http 5050
   ```

4. Copy the ngrok URL (e.g., `https://abc123.ngrok.io`)

5. Go to [Fireflies Settings > Developer](https://app.fireflies.ai/settings) and paste:
   ```
   https://abc123.ngrok.io/webhook/fireflies
   ```

Now action items will sync automatically when meetings end!

### Option B: Scheduled polling (simpler)

Add to crontab (`crontab -e`):
```bash
# Check every 30 minutes
*/30 * * * * cd /path/to/fireflies-to-notes && python3 fireflies_notes.py --recent 1
```

### Option C: macOS LaunchAgent (persistent)

1. Create `~/Library/LaunchAgents/com.fireflies.notes.plist`:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
       <key>Label</key>
       <string>com.fireflies.notes</string>
       <key>ProgramArguments</key>
       <array>
           <string>/usr/bin/python3</string>
           <string>/path/to/fireflies_notes.py</string>
           <string>--recent</string>
           <string>1</string>
       </array>
       <key>StartInterval</key>
       <integer>1800</integer>
       <key>RunAtLoad</key>
       <true/>
   </dict>
   </plist>
   ```

2. Load it:
   ```bash
   launchctl load ~/Library/LaunchAgents/com.fireflies.notes.plist
   ```

## Commands

```bash
# Test API connection
python3 fireflies_notes.py --test

# Sync most recent meeting
python3 fireflies_notes.py --recent 1

# Sync last 5 meetings
python3 fireflies_notes.py --recent 5

# Sync specific transcript
python3 fireflies_notes.py --transcript-id ABC123XYZ
```

## Configuration

Set environment variables:
```bash
export FIREFLIES_API_KEY="your-api-key"  # Required - get from https://app.fireflies.ai/settings
export FIREFLIES_WEBHOOK_SECRET="your-secret"  # Optional - for webhook verification
```

Or create a `.env` file and source it before running.
