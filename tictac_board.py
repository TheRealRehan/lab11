from dataclasses import dataclass, field
import redis
import json

r = redis.Redis(
    host="ai.thewcl.com",
    port=6379,
    password="atmega328",
    decode_responses=True
)

REDIS_GAME_KEY = "tic_tac_toe:game_state:5"

@dataclass
class TicTacBoard:
    state: str = "is_playing"
    player_turn: str = "x"
    positions: list = field(default_factory=lambda: [""] * 9)

    def serialize(self):
        board_dict = {
            "state": self.state,
            "player_turn": self.player_turn,
            "positions": self.positions
        }
        return json.dumps(board_dict)

    def save_to_redis(self):
        json_string = self.serialize()
        game_data = json.loads(json_string)
        r.json().set(REDIS_GAME_KEY, ".", game_data)

    @classmethod
    def load_from_redis(cls):
        game_data = r.json().get(REDIS_GAME_KEY)
        if game_data is None:
            print("No game data found in Redis.")
            return cls()
        return cls(**game_data)

    def reset(self):
        self.state = "is_playing"
        self.player_turn = "x"
        self.positions = [""] * 9
        self.save_to_redis()

    def is_my_turn(self, i_am):
        return self.state == "is_playing" and self.player_turn == i_am

    def make_move(self, index: int):
        if self.state != "is_playing":
            return "Game Over"
        if not 0 <= index <= 8:
            print("Invalid index, must be between 0 and 8.")
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

