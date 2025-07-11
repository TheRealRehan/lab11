import asyncio
import json
import argparse
import redis.asyncio as redis
import os
from tictac_board import TicTacToeBoard

GAME_KEY = "tictactoe:board"
CHANNEL = "tictactoe:updates"

async def publish_update(redis_client, board_dict):
    await redis_client.publish(CHANNEL, json.dumps(board_dict))

async def subscribe_updates(redis_client, player_mark):
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(CHANNEL)

    async for message in pubsub.listen():
        if message["type"] == "message":
            board_data = json.loads(message["data"])
            if board_data["current_player"] == player_mark:
                print("\nYour turn:")
            else:
                print(f"\nWaiting for {board_data['current_player']}...")
            print(json.dumps(board_data, indent=2))

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--player", required=True, choices=["x", "o"])
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    # ✅ Redis client must be created INSIDE this function
    student_number = os.getenv("STUDENT_NUMBER", "0")
    redis_url = f"redis://default:atmega328@ai.thewcl.com:6379/{student_number}"
    redis_client = redis.Redis.from_url(redis_url)

    if args.reset:
        board = TicTacToeBoard()
        await board.save_to_redis(redis_client, GAME_KEY)
        await publish_update(redis_client, board.to_dict())
        print("Game reset.")
        return

    board = await TicTacToeBoard.load_from_redis(redis_client, GAME_KEY)
    print(json.dumps(board.to_dict(), indent=2))

    asyncio.create_task(subscribe_updates(redis_client, args.player))

    while True:
        if board.winner or board.draw:
            await asyncio.sleep(1)
            continue

        if board.current_player != args.player:
            await asyncio.sleep(1)
            board = await TicTacToeBoard.load_from_redis(redis_client, GAME_KEY)
            continue

        try:
            index = int(input("Enter your move (0-8): "))
        except ValueError:
            print("Please enter a valid number between 0 and 8.")
            continue

        result = board.make_move(args.player, index)
        print(result["message"])

        if result["success"]:
            await board.save_to_redis(redis_client, GAME_KEY)
            await publish_update(redis_client, board.to_dict())

if __name__ == "__main__":
    asyncio.run(main())
