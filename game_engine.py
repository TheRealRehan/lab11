import os
import sys
import json
import asyncio
import argparse
import redis.asyncio as redis
import httpx
import websockets

# ── Required environment config ──
try:
    STUDENT_NUMBER = os.environ["STUDENT_NUMBER"]
    REDIS_PASSWORD = os.environ["REDIS_PASSWORD"]
    REDIS_HOST     = os.environ["REDIS_HOST"]
    REDIS_PORT     = os.environ["REDIS_PORT"]
except KeyError as e:
    print(f"❌ Missing required environment variable: {e}")
    sys.exit(1)

REDIS_URL = f"redis://default:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{STUDENT_NUMBER}"
r = redis.from_url(REDIS_URL, decode_responses=True)

# ── Redis Key and Pub/Sub Channel ──
REDIS_KEY = f"tic_tac_toe:game_state:{STUDENT_NUMBER}"
PUBSUB_CHANNEL = "ttt_game_state_changed"

# ── Track WebSocket connections ──
connected_clients = set()

# ── Display the board from JSON ──
def display_board(board_list):
    for i in range(0, 9, 3):
        row = [" " if cell is None else cell for cell in board_list[i:i+3]]
        print(row)
    print()

# ── CLI argument parsing ──
def parse_args():
    parser = argparse.ArgumentParser(description="Tic-Tac-Toe HTTP Client")
    parser.add_argument("--player", choices=["x", "o"], required=True)
    parser.add_argument("--reset", action="store_true")
    return parser.parse_args()

# ── Redis helpers ─
async def save_to_redis(board):
    await r.set(REDIS_KEY, json.dumps(board))

async def load_from_redis():
    data = await r.get(REDIS_KEY)
    if not data:
        return {"board": [None] * 9, "current_player": "x", "winner": None, "draw": False}
    return json.loads(data)

# ── Broadcast updated state to all connected clients ─
async def broadcast_state(board):
    if not connected_clients:
        return
    message = json.dumps({"positions": board["board"]})
    await asyncio.gather(*(client.send(message) for client in connected_clients))

# ── Handle moves and game logic ─
async def handle_board_state(player):
    async with httpx.AsyncClient() as client:
        # 1. GET /state
        response = await client.get("http://localhost:8000/state")
        game = response.json()

        display_board(game["board"])

        if game["winner"]:
            print(f"🏁 Game Over! Player {game['winner']} wins!")
            return
        if game["draw"]:
            print("🏁 Game ended in a draw.")
            return

        if player == game["current_player"]:
            try:
                index = int(input(f"Your move ({player}): "))
            except ValueError:
                print("⚠️ Please enter a valid number (0–8).")
                return

            move_payload = {"player": player, "index": index}
            move_response = await client.post("http://localhost:8000/move", json=move_payload)
            result = move_response.json()
            print(result["message"])

            board = await load_from_redis()
            await broadcast_state(board)
        else:
            print(f"⏳ Waiting for {game['current_player']} to move...")

# ── Pub/Sub Listener ─
async def listen_for_updates(player):
    pubsub = r.pubsub()
    await pubsub.subscribe(PUBSUB_CHANNEL)
    print(f"📡 Subscribed as {player} on '{PUBSUB_CHANNEL}'")

    await handle_board_state(player)

    async for msg in pubsub.listen():
        if msg.get("type") == "message":
            await handle_board_state(player)
            state = await load_from_redis()
            if state["winner"] or state["draw"]:
                print("👋 Game over. Exiting.")
                break

# ── WebSocket Server ─
async def websocket_broadcaster():
    async def handler(websocket):
        connected_clients.add(websocket)
        try:
            board = await load_from_redis()
            await websocket.send(json.dumps({"positions": board["board"]}))
            await asyncio.Future()  # Keep open
        except:
            pass
        finally:
            connected_clients.remove(websocket)

    port = 8700 + int(STUDENT_NUMBER)
    print(f"🌐 WebSocket server running on ws://localhost:{port}")
    await websockets.serve(handler, "0.0.0.0", port, reuse_port=True)

# ── Main Entrypoint ─
async def main():
    args = parse_args()

    if args.reset:
        board = {"board": [None] * 9, "current_player": "x", "winner": None, "draw": False}
        await save_to_redis(board)
        await broadcast_state(board)
        print("✅ Board has been reset.")
        return

    await asyncio.gather(
        listen_for_updates(args.player),
        websocket_broadcaster()
    )

if __name__ == "__main__":
    asyncio.run(main())

