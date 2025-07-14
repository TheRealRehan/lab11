import os
import sys
import argparse
import asyncio
import redis.asyncio as redis
import httpx


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


# ── Placeholder: this will be updated in Part 2 ──
async def handle_board_state(player: str):
    async with httpx.AsyncClient() as client:
        # 1. GET /state
        try:
            response = await client.get("http://localhost:8000/state")
            game = response.json()
        except Exception as e:
            print(f"❌ Failed to fetch game state: {e}")
            return

        # 2. Display the board
        display_board(game["board"])

        # 3. Game over?
        if game["winner"]:
            print(f"🏁 Game Over! Player {game['winner']} wins!")
            return
        if game["draw"]:
            print("🏁 Game ended in a draw.")
            return

        # 4. If it's your turn, prompt for move
        if player == game["current_player"]:
            try:
                index = int(input(f"Your move ({player}): "))
            except ValueError:
                print("⚠️ Please enter a valid number (0-8).")
                return

            # 5. POST /move
            move_payload = {"player": player, "index": index}
            try:
                move_response = await client.post("http://localhost:8000/move", json=move_payload)
                result = move_response.json()
                print(result["message"])
            except Exception as e:
                print(f"❌ Move failed: {e}")
        else:
            print(f"⏳ Waiting for {game['current_player']} to move...")



# ── Pub/Sub Listener ──
async def listen_for_updates(player: str):
    pubsub = r.pubsub()
    await pubsub.subscribe(PUBSUB_CHANNEL)
    print(f"📡 Subscribed as {player} on '{PUBSUB_CHANNEL}'")

    await handle_board_state(player)

    async for msg in pubsub.listen():
        if msg.get("type") == "message":
            await handle_board_state(player)


# ── Main ──
async def main():
    args = parse_args()

    async with httpx.AsyncClient() as client:
        if args.reset:
            try:
                response = await client.post("http://localhost:8000/reset")
                result = response.json()
                print(result["message"])
            except Exception as e:
                print(f"❌ Reset failed: {e}")
            return

    await listen_for_updates(args.player)


if __name__ == "__main__":
    asyncio.run(main())
