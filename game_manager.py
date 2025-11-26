# game_manager.py
import threading
from game import Game

class GameManager:
    """Manages all active scalable games."""

    def __init__(self):
        self.games = {}
        self.lock = threading.Lock()
        self.next_game_id = 1

    def create_game(self, max_players):
        with self.lock:
            gid = self.next_game_id
            self.next_game_id += 1
            game = Game(gid, max_players)
            self.games[gid] = game
        return game

    def list_games(self):
        return list(self.games.values())

    def get_game(self, gid):
        return self.games.get(gid)
