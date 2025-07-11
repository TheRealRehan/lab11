from fastapi import FastAPI, Request, Body
from tictac_board import TicTacToeBoard
import redis.asyncio as redis
import os

app = FastAPI()


# ── Load environment variables (same as before) ──
STUDENT_NUMBER = os.getenv("STUDENT_NUMBER", "0")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
REDIS_HOST     = os.getenv("REDIS_HOST")
REDIS_PORT     = os.getenv("REDIS_PORT")

REDIS_URL = f"redis://default:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{STUDENT_NUMBER}"
r = redis.from_url(REDIS_URL, decode_responses=True)
REDIS_KEY = f"tic_tac_toe:game_state:{STUDENT_NUMBER}"

# ── Create the FastAPI app ──



#Loads the current board from Redis
#Returns its data as a dictionary (which FastAPI converts to JSON)
@app.get("/state")
async def get_game_state():
    board = await TicTacToeBoard.load_from_redis(r, REDIS_KEY)
    return board.to_dict()


#Accepts a JSON payload like {"player": "x", "index": 4}
#Calls make_move()
#Returns the result (success, message, updated board)
@app.post("/move")
async def post_move(payload: dict = Body(...)):
    player = payload.get("player")
    index = payload.get("index")
    
    board = await TicTacToeBoard.load_from_redis(r, REDIS_KEY)
    result = board.make_move(player, index)
    
    if result["success"]:
        await board.save_to_redis(r, REDIS_KEY)
    return result

#resets the board in memory
#Saves it in Redis
#Returns confirmation + new board state
@app.post("/reset")
async def reset_board():
    board = TicTacToeBoard()
    board.reset()
    await board.save_to_redis(r, REDIS_KEY)
    return {
        "success": True,
        "message": "Board has been reset.",
        "board": board.to_dict()
    }


