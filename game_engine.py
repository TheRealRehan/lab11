from main import TicTacBoard

def main():
    print("Main function has started")
    board = TicTacBoard()

    player = input("Choose your player ('x' or 'o'): ").strip().lower()
    if player not in ("x", "o"):
        print("Invalid player. Must be 'x' or 'o'.")
        return

    print("\nStarting game. Enter positions 0–8 to play:")
    board.display()

    while board.state == "is_playing":
        if board.is_my_turn(player):
            try:
                move = int(input(f"Your move ({player}): "))
                board.make_move(move)
            except ValueError:
                print("Please enter a number between 0 and 8.")
        else:
            print(f"Waiting for {board.player_turn}'s move... (simulate by entering move)")
            try:
                move = int(input(f"Move for {board.player_turn}: "))
                board.make_move(move)
            except ValueError:
                print("Please enter a number between 0 and 8.")

        board.display()

    print(f"Game ended. Final state: {board.state}")
    
    

if __name__ == "__main__":
    main()
