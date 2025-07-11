import os
import sys
import argparse
import asyncio
import redis.asyncio as redis
from tictac_board import TicTacToeBoard

# ── Require all Redis config from environment ──
try:
    STUDENT_NUMBER  = os.environ["STUDENT_NUMBER"]
    REDIS_PASSWORD  = os.environ["REDIS_PASSWORD"]
    REDIS_HOST      = os.environ["REDIS_HOST"]
    REDIS_PORT      = os.environ["REDIS_PORT"]
except KeyError as e:
    print(f"❌ Missing required environment variable: {e}")
    sys.exit(1)

# ── Build Redis URL from environment ──
REDIS_URL = f"redis://default:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{STUDENT_NUMBER}"
r = redis.from_url(REDIS_URL, decode_responses=True)

# ── Redis key and pub/sub channel ──
REDIS_KEY      = f"tic_tac_toe:game_state:{STUDENT_NUMBER}"
PUBSUB_CHANNEL = "ttt_game_state_changed"

# ── Pub/Sub game flow ──

async def handle_board_state(player: str) -> bool:
    """
    Return False if the game is over (win or draw), True otherwise.
    """
    board = await TicTacToeBoard.load_from_redis(r, REDIS_KEY)
    display_board(board.board)

    # ——— Game‐over check ———
    if board.winner or board.draw:
        if board.winner:
            print(f"🏁 Game over! Player {board.winner} wins!")
        else:
            print("🏁 Game ended in a draw.")
        return False   # signal “no more turns”

    # ——— Still playing ———
    if board.is_my_turn(player):
        raw = input(f"Your move ({player}): ")
        try:
            idx = int(raw)
        except ValueError:
            print("▶ Please enter a number between 0 and 8.")
            return True

        result = board.make_move(player, idx)
        print(result["message"])
        if result["success"]:
            await board.save_to_redis(r, REDIS_KEY)
            await r.publish(PUBSUB_CHANNEL, f"{player} moved")
    else:
        print(f"⏳ Waiting for {board.current_player} to move...")

    return True  # signal “keep listening”


async def listen_for_updates(player: str):
    pubsub = r.pubsub()
    await pubsub.subscribe(PUBSUB_CHANNEL)
    print(f"📡 Subscribed as {player} on '{PUBSUB_CHANNEL}'")

    # First call
    keep_going = await handle_board_state(player)
    if not keep_going:
        return

    # Subsequent calls on each message
    async for msg in pubsub.listen():
        if msg.get("type") == "message":
            keep_going = await handle_board_state(player)
            if not keep_going:
                # Cleanly exit the loop when the game is over
                break
            
# ── CLI ──

def parse_args():
    parser = argparse.ArgumentParser(description="Tic-Tac-Toe with Redis + Pub/Sub")
    parser.add_argument("--player", choices=["x", "o"], required=True, help="Choose player X or O")
    parser.add_argument("--reset", action="store_true", help="Reset the board before playing")
    return parser.parse_args()


# ── Board UI ──

def display_board(board_list):
    for i in range(0, 9, 3):
        row = [" " if cell is None else cell for cell in board_list[i:i+3]]
        print(row)
    print()


# ── Entrypoint ──

async def main():
    args = parse_args()

    if args.reset:
        board = TicTacToeBoard()
        board.reset()
        await board.save_to_redis(r, REDIS_KEY)
        print("✅ Board reset.")
        return

    await listen_for_updates(args.player)


if __name__ == "__main__":
    asyncio.run(main())
