from dataclasses import dataclass, field, asdict
import json

@dataclass
class TicTacToeBoard:
    board: list = field(default_factory=lambda: [None] * 9)
    current_player: str = "x"
    winner: str = None
    draw: bool = False

    def serialize(self) -> str:
        """Return board state as a JSON string."""
        return json.dumps(asdict(self))
    
    def to_dict(self):
        return asdict(self)

    def reset(self):
        """Reset the board to the initial empty state."""
        self.board = [None] * 9
        self.current_player = "x"
        self.winner = None
        self.draw = False

    def is_my_turn(self, player: str) -> bool:
        """True if it's the player's turn and game is still ongoing."""
        return (
            self.current_player == player
            and self.winner is None
            and not self.draw
        )

    def make_move(self, player: str, index: int) -> dict:
        """Attempt to make a move. Return result dict with message + success flag."""
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
            (0, 3, 6), (1, 4, 7), (2, 5, 8),  # cols
            (0, 4, 8), (2, 4, 6)              # diags
        ]
        for a, b, c in win_positions:
            if self.board[a] and self.board[a] == self.board[b] == self.board[c]:
                self.winner = self.board[a]
                return
        if all(cell is not None for cell in self.board):
            self.draw = True

    # Redis persistence methods

    async def save_to_redis(self, redis_client, game_key):
        """Save board state as JSON to Redis."""
        await redis_client.set(game_key, self.serialize())

    @classmethod
    async def load_from_redis(cls, redis_client, game_key):
        """Load board state from Redis and return a TicTacToeBoard instance."""
        data = await redis_client.get(game_key)
        if data:
            obj = json.loads(data)
            return cls(**obj)
        return cls()
