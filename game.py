# game.py
class Game:
    """
    Scalable Tic-Tac-Toe game.
    Supports x players with board size = (x + 1) × (x + 1).
    Win condition is always 3 in a row.
    """

    BASE_SYMBOLS = ["X", "O", "∆", "□", "★", "✓", "♣", "♠"] # Extendable for more players
    def __init__(self, game_id, max_players):
        self.game_id = game_id
        self.max_players = max_players
        self.players = []   # (conn, symbol)
        self.board_size = max_players + 1
        self.board = [[" " for _ in range(self.board_size)] for _ in range(self.board_size)]

        self.turn_index = 0  # Index of player whose turn it is
        self.game_over = False

    # -----------------------------
    #      PLAYERS
    # -----------------------------
    def add_player(self, conn):
        if len(self.players) >= self.max_players:
            return None

        symbol = self.BASE_SYMBOLS[len(self.players)]
        self.players.append((conn, symbol))
        return symbol

    def current_symbol(self):
        """Returns the symbol of the player whose turn it is."""
        if not self.players:
            return None
        return self.players[self.turn_index][1]

    def advance_turn(self):
        """Moves to the next player's turn."""
        self.turn_index = (self.turn_index + 1) % len(self.players)

    # -----------------------------
    #      BOARD FUNCTIONS
    # -----------------------------
    def is_valid_move(self, row, col):
        if self.game_over:
            return False
        if row < 0 or col < 0 or row >= self.board_size or col >= self.board_size:
            return False
        return self.board[row][col] == " "

    def apply_move(self, symbol, row, col):
        self.board[row][col] = symbol

    # -----------------------------
    #    SCALABLE WIN CHECK
    # -----------------------------
    def check_winner(self, symbol):
        """Check if symbol has 3 consecutive anywhere."""

        N = self.board_size
        target = symbol

        # Check rows
        for r in range(N):
            for c in range(N - 2):
                if self.board[r][c] == target and \
                   self.board[r][c+1] == target and \
                   self.board[r][c+2] == target:
                    return True

        # Check columns
        for c in range(N):
            for r in range(N - 2):
                if self.board[r][c] == target and \
                   self.board[r+1][c] == target and \
                   self.board[r+2][c] == target:
                    return True

        # Check diagonals (top-left → bottom-right)
        for r in range(N - 2):
            for c in range(N - 2):
                if self.board[r][c] == target and \
                   self.board[r+1][c+1] == target and \
                   self.board[r+2][c+2] == target:
                    return True

        # Check diagonals (bottom-left → top-right)
        for r in range(2, N):
            for c in range(N - 2):
                if self.board[r][c] == target and \
                   self.board[r-1][c+1] == target and \
                   self.board[r-2][c+2] == target:
                    return True

        return False

    def is_draw(self):
        for row in self.board:
            if " " in row:
                return False
        return True
