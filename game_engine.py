import argparse
import asyncio
import redis.asyncio as redis
from tictac_board import TicTacBoard

# Redis setup
r = redis.Redis(
    host="ai.thewcl.com",
    port=6379,
    password="atmega328",
    decode_responses=True
)

REDIS_KEY = "tic_tac_toe:game_state:5"
PUBSUB_CHANNEL = "ttt_game_state_changed"

# Save board to Redis (as string)
async def save_to_redis(board):
    await r.set(REDIS_KEY, board.serialize())

# Load board from Redis
async def load_from_redis():
    data = await r.get(REDIS_KEY)
    if data is None:
        return TicTacBoard()
    return TicTacBoard.deserialize(data)

# Game logic when it's your turn
async def handle_board_state(i_am):
    board = await load_from_redis()
    board.display()

    if board.is_my_turn(i_am):
        try:
            move = int(input(f"Your move ({i_am}): "))
            board.make_move(move)
            await save_to_redis(board)
            await r.publish(PUBSUB_CHANNEL, f"{i_am} moved")
        except ValueError:
            print("Please enter a number between 0 and 8.")
    else:
        print("Waiting for opponent...")

# Listen for changes
async def listen_for_updates(i_am):
    pubsub = r.pubsub()
    await pubsub.subscribe(PUBSUB_CHANNEL)
    print(f"📡 Subscribed to '{PUBSUB_CHANNEL}' as {i_am}")

    await handle_board_state(i_am)

    async for message in pubsub.listen():
        if message["type"] == "message":
            await handle_board_state(i_am)

# Parse CLI flags
def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--player", choices=["x", "o"])
    parser.add_argument("--reset", action="store_true")
    return parser.parse_args()

# Main logic
async def main():
    args = parse_args()

    if args.reset:
        board = TicTacBoard()
        board.reset()
        await save_to_redis(board)
        print("✅ Board reset.")
        return

    if not args.player:
        print("❌ Please provide --player x or o")
        return

    await listen_for_updates(args.player)

if __name__ == "__main__":
    asyncio.run(main())
