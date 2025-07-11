from dataclasses import dataclass, field, asdict
import json

@dataclass
class TicTacToeBoard:
    board: list = field(default_factory=lambda: [None] * 9)
    current_player: str = "x"
    winner: str = None
    draw: bool = False

    def make_move(self, player: str, index: int) -> dict:
        if self.winner or self.draw:
            return {
                "success": False,
                "message": f"Game is already over. Winner: {self.winner}" if self.winner else "Game ended in a draw."
            }

        if player != self.current_player:
            return {
                "success": False,
                "message": f"It's not your turn. It's {self.current_player}'s turn."
            }

        if index < 0 or index >= 9 or self.board[index] is not None:
            return {
                "success": False,
                "message": "Invalid move: index out of bounds or spot already taken."
            }

        self.board[index] = player
        self._check_winner_or_draw()

        message = f"Player {player} moved to spot {index}."
        if self.winner:
            message += f" Player {player} wins!"
        elif self.draw:
            message += " The game is a draw."
        else:
            self._switch_turns()
            message += f" It's {self.current_player}'s turn next."

        return {
            "success": True,
            "message": message,
            "board": self.board
        }

    def _switch_turns(self):
        self.current_player = "o" if self.current_player == "x" else "x"

    def _check_winner_or_draw(self):
        win_positions = [
            (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
            (0, 4, 8), (2, 4, 6)              # diagonals
        ]
        for a, b, c in win_positions:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                self.winner = self.board[a]
                return
        if all(cell is not None for cell in self.board):
            self.draw = True

    def to_dict(self):
        return asdict(self)

    async def save_to_redis(self, redis_client, game_key):
        await redis_client.set(game_key, json.dumps(self.to_dict()))

    @classmethod
    async def load_from_redis(cls, redis_client, game_key):
        data = await redis_client.get(game_key)
        if data:
            obj = json.loads(data)
            return cls(**obj)
        return cls()
