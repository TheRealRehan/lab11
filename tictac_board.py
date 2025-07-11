from dataclasses import dataclass, field
import json

@dataclass
class TicTacBoard:
    state: str = "is_playing"
    player_turn: str = "x"
    positions: list = field(default_factory=lambda: [""] * 9)

    def serialize(self):
        return json.dumps({
            "state": self.state,
            "player_turn": self.player_turn,
            "positions": self.positions
        })

    @staticmethod
    def deserialize(data: str):
        obj = json.loads(data)
        return TicTacBoard(**obj)

    def reset(self):
        self.state = "is_playing"
        self.player_turn = "x"
        self.positions = [""] * 9

    def is_my_turn(self, i_am):
        return self.state == "is_playing" and self.player_turn == i_am

    def make_move(self, index: int):
        if self.state != "is_playing":
            print("Game Over")
            return
        if not 0 <= index <= 8:
            print("Invalid index, must be between 0 and 8")
            return
        if self.positions[index] != "":
            print("Position already taken.")
            return

        self.positions[index] = self.player_turn

        if self.check_winner():
            self.state = f"{self.player_turn}_won"
            print(f"Player {self.player_turn} wins!")
            return

        if self.check_draw():
            self.state = "draw"
            print("It's a draw!")
            return

        self.switch_turn()

    def check_winner(self):
        win_patterns = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),
            (0, 3, 6), (1, 4, 7), (2, 5, 8),
            (0, 4, 8), (2, 4, 6)
        ]
        for a, b, c in win_patterns:
            if self.positions[a] == self.positions[b] == self.positions[c] != "":
                return True
        return False

    def check_draw(self):
        return "" not in self.positions and not self.check_winner()

    def switch_turn(self):
        self.player_turn = "o" if self.player_turn == "x" else "x"

    def display(self):
        for i in range(0, 9, 3):
            print(self.positions[i:i+3])
        print()

