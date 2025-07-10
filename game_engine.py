from tictac_board import TicTacBoard
import argparse


# 🧠 Parse command-line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--player", choices=["x", "o"], required=True)
parser.add_argument("--reset", action="store_true")
args = parser.parse_args()

def main():
    player = args.player

    # 🧹 Reset the board if --reset was passed
    if args.reset:
        board = TicTacBoard()
        board.reset()
        board.save_to_redis()
        print("Game was reset.")
    else:
        board = TicTacBoard.load_from_redis()

    board.display()

    print("\nStarting game. Enter positions 0–8 to play:")

   
    while board.state == "is_playing":
        if board.is_my_turn(player):
            try:
                move = int(input(f"Your move ({player}): "))
                board.make_move(move)
                board.save_to_redis()
            except ValueError:
                print("Please enter a number between 0 and 8.")
        else:
            print(f"Waiting for {board.player_turn}'s move... (simulate by entering move)")
            try:
                move = int(input(f"Move for {board.player_turn}: "))
                board.make_move(move)
                board.save_to_redis()
            except ValueError:
                print("Please enter a number between 0 and 8.")

        board.display()

    # 🏁 Game over
    print(f"Game ended. Final state: {board.state}")

if __name__ == "__main__":
    main()
