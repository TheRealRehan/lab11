import asyncio
import websockets
import os
import json
import sys

# ── Load required WebSocket config from env ──
try:
    STUDENT_NUMBER = os.environ["STUDENT_NUMBER"]
except KeyError:
    print("❌ Please export STUDENT_NUMBER in your terminal (e.g. export STUDENT_NUMBER=05)")
    sys.exit(1)

WEBSOCKET_URL = f"ws://ai.thewcl.com:87{STUDENT_NUMBER}"


# ── Connect and listen for updates ──
async def listen_for_updates():
    try:
        async with websockets.connect(WEBSOCKET_URL) as websocket:
            print(f"✅ Connected to {WEBSOCKET_URL}")
            async for message in websocket:
                try:
                    data = json.loads(message)
                    positions = data["positions"]
                    render_board(positions)
                except (json.JSONDecodeError, KeyError):
                    print("⚠️ Invalid message format. Expected JSON with 'positions'.")
    except Exception as e:
        print(f"❌ Connection failed: {e}")


# ── Draw the board ──
def render_board(positions):
    os.system("cls" if os.name == "nt" else "clear")
    display = []

    for i, val in enumerate(positions):
        if val and val.lower() in ("x", "o"):
            display.append(val.upper())
        else:
            display.append(str(i))

    print(f" {display[0]} | {display[1]} | {display[2]}")
    print("---+---+---")
    print(f" {display[3]} | {display[4]} | {display[5]}")
    print("---+---+---")
    print(f" {display[6]} | {display[7]} | {display[8]}")


# ── Run the listener ──
if __name__ == "__main__":
    asyncio.run(listen_for_updates())
