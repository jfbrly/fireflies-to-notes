#!/usr/bin/env python3
"""
Fireflies.ai to Apple Notes Integration
Fetches action items from Fireflies and appends to Apple Notes.

Requirements: requests (pip install requests)
Run on macOS only (uses AppleScript).
"""

import requests
import subprocess
import json
import os
from datetime import datetime

FIREFLIES_API_KEY = os.environ.get("FIREFLIES_API_KEY", "")
FIREFLIES_ENDPOINT = "https://api.fireflies.ai/graphql"
NOTES_NAME = "TODO and Work!"

def fetch_action_items(transcript_id: str) -> dict:
    """Fetch action items for a specific transcript."""
    query = """
    query Transcript($transcriptId: String!) {
        transcript(id: $transcriptId) {
            id
            title
            date
            summary {
                action_items
            }
        }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {FIREFLIES_API_KEY}"
    }
    
    response = requests.post(
        FIREFLIES_ENDPOINT,
        json={"query": query, "variables": {"transcriptId": transcript_id}},
        headers=headers
    )
    response.raise_for_status()
    return response.json()

def fetch_recent_transcripts(limit: int = 5) -> list:
    """Fetch recent transcripts."""
    query = """
    query Transcripts($limit: Int) {
        transcripts(limit: $limit) {
            id
            title
            date
            summary {
                action_items
            }
        }
    }
    """
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {FIREFLIES_API_KEY}"
    }
    
    response = requests.post(
        FIREFLIES_ENDPOINT,
        json={"query": query, "variables": {"limit": limit}},
        headers=headers
    )
    response.raise_for_status()
    data = response.json()
    return data.get("data", {}).get("transcripts", [])

def format_action_items(transcript: dict) -> str:
    """Format action items for Apple Notes (HTML)."""
    title = transcript.get("title", "Unknown Meeting")
    date = transcript.get("date", "")
    action_items = transcript.get("summary", {}).get("action_items", "")
    
    if not action_items:
        return None
    
    # Format date
    if date:
        try:
            dt = datetime.fromtimestamp(int(date) / 1000)
            date_str = dt.strftime("%Y-%m-%d %H:%M")
        except:
            date_str = str(date)
    else:
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Build HTML for Notes
    html = f"""<h2>📋 {title}</h2>
<p><i>{date_str}</i></p>
<p>{action_items}</p>
<hr>
"""
    return html

def prepend_to_apple_note(note_name: str, content: str) -> bool:
    """Prepend content to an Apple Note using AppleScript."""
    # Escape content for AppleScript
    escaped_content = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
    
    applescript = f'''
tell application "Notes"
    set targetNote to missing value
    repeat with aNote in notes of default account
        if name of aNote is "{note_name}" then
            set targetNote to aNote
            exit repeat
        end if
    end repeat
    
    if targetNote is missing value then
        -- Create note if it doesn't exist
        set targetNote to make new note at default account with properties {{name:"{note_name}", body:"{escaped_content}"}}
    else
        -- Prepend to existing note
        set currentBody to body of targetNote
        set body of targetNote to "{escaped_content}" & currentBody
    end if
    
    return "success"
end tell
'''
    
    try:
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode == 0:
            print(f"✅ Added to note: {note_name}")
            return True
        else:
            print(f"❌ AppleScript error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("❌ AppleScript timed out")
        return False
    except FileNotFoundError:
        print("❌ osascript not found - this script must run on macOS")
        return False

def process_transcript(transcript_id: str) -> bool:
    """Process a single transcript and add its action items to Notes."""
    print(f"📥 Fetching transcript: {transcript_id}")
    
    data = fetch_action_items(transcript_id)
    transcript = data.get("data", {}).get("transcript")
    
    if not transcript:
        print("❌ Transcript not found")
        return False
    
    content = format_action_items(transcript)
    if not content:
        print("ℹ️ No action items in this transcript")
        return False
    
    return prepend_to_apple_note(NOTES_NAME, content)

def process_recent(limit: int = 1) -> int:
    """Process recent transcripts."""
    print(f"📥 Fetching {limit} recent transcript(s)...")
    
    transcripts = fetch_recent_transcripts(limit)
    processed = 0
    
    for transcript in transcripts:
        content = format_action_items(transcript)
        if content:
            if prepend_to_apple_note(NOTES_NAME, content):
                processed += 1
    
    print(f"✅ Processed {processed} transcript(s)")
    return processed

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fireflies to Apple Notes")
    parser.add_argument("--transcript-id", "-t", help="Process specific transcript ID")
    parser.add_argument("--recent", "-r", type=int, default=1, help="Process N recent transcripts")
    parser.add_argument("--test", action="store_true", help="Test API connection")
    
    args = parser.parse_args()
    
    if args.test:
        print("🔍 Testing Fireflies API connection...")
        transcripts = fetch_recent_transcripts(1)
        if transcripts:
            print(f"✅ Connected! Found transcript: {transcripts[0].get('title')}")
        else:
            print("⚠️ Connected but no transcripts found")
        return
    
    if args.transcript_id:
        process_transcript(args.transcript_id)
    else:
        process_recent(args.recent)

if __name__ == "__main__":
    main()
